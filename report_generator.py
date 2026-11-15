import os
import glob
import time
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError, ClientError

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("🚨 GOOGLE_API_KEY not found in .env file!")
    exit(1)

client = genai.Client(api_key=api_key)

print("🔄 Loading compliance documents...")
docs = {}
for path in glob.glob("./data/**/*.txt", recursive=True):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        docs[os.path.basename(path)] = f.read()

combined_context = "\n\n".join([f"--- FILE: {name} ---\n{content}" for name, content in docs.items()])

output_file = "evaluation_results.csv"

# Checkpoint / Resumability Logic
if os.path.exists(output_file):
    print(f"📂 Found existing progress in {output_file}. Resuming automatically...")
    df = pd.read_csv(output_file)
else:
    print("📂 Loading test_set.csv...")
    df = pd.read_csv("test_set.csv")
    if "Prediction" not in df.columns:
        df["Prediction"] = ""
    if "Match" not in df.columns:
        df["Match"] = False

print(f"🚀 Running/Resuming evaluation across {len(df)} test prompts...")

for index, row in df.iterrows():
    # Skip rows that already have a successful prediction saved
    if pd.notna(row["Prediction"]) and str(row["Prediction"]).strip() != "":
        continue
        
    prompt_text = row["Prompt"]
    
    eval_prompt = f"""
    You are WatchdogAI compliance auditor. Evaluate the following user scenario strictly against the source documents.
    
    SOURCE DOCUMENTS:
    {combined_context}
    
    SCENARIO TO EVALUATE:
    {prompt_text}
    
    INSTRUCTIONS:
    Output ONLY one single word representing your verdict based strictly on the policies: [Supported], [Contradicted], or [Unverified]. Do not write anything else.
    """
    
    pred = "Unverified"
    
    # Try models with built-in retry/backoff for rate limits
    for model_name in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-1.5-flash"]:
        try:
            res = client.models.generate_content(model=model_name, contents=eval_prompt)
            text = res.text.strip().capitalize()
            if "Contradicted" in text:
                pred = "Contradicted"
            elif "Supported" in text:
                pred = "Supported"
            elif "Unverified" in text or "Unverifiable" in text:
                pred = "Unverified"
            else:
                pred = text if text in ["Supported", "Contradicted", "Unverified"] else "Unverified"
            break
        except (ServerError, ClientError) as e:
            # If rate-limited (429), wait a few seconds and try next model
            time.sleep(4)
            continue
            
    df.at[index, "Prediction"] = pred
    df.at[index, "Match"] = pred == str(row["Ground Truth"]).strip().capitalize()
    
    # Save progress immediately (Checkpoint)
    df.to_csv(output_file, index=False)
    
    print(f"[{index+1}/{len(df)}] Prompt: '{prompt_text[:30]}...' -> Prediction: {pred} | Expected: {row['Ground Truth']}")
    
    # 3-second delay between requests to completely prevent rate limit spikes
    time.sleep(3)

# Filter completed rows for final stats
completed_df = df[df["Prediction"].notna() & (df["Prediction"] != "")]
accuracy = (completed_df["Match"].sum() / len(completed_df)) * 100 if len(completed_df) > 0 else 0

print("\n===============================")
print(f"🎯 EVALUATION COMPLETE: {accuracy:.2f}% Accuracy")
print("===============================\n")

# --- GENERATE DEMO GRAPH ---
categories = ["Contradicted", "Supported", "Unverified"]
match_counts = [
    len(completed_df[(completed_df["Ground Truth"].str.strip().str.capitalize() == cat) & (completed_df["Match"] == True)]) for cat in categories
]
total_counts = [
    len(completed_df[completed_df["Ground Truth"].str.strip().str.capitalize() == cat]) for cat in categories
]

fig, ax = plt.subplots(figsize=(8, 5))
fig.patch.set_facecolor('#000000')
ax.set_facecolor('#000000')

ax.bar(categories, total_counts, color='#333333', label='Total Test Cases', width=0.5)
ax.bar(categories, match_counts, color='#00E620', label='Correctly Audited', width=0.5)

ax.set_ylabel("Number of Test Prompts", color='#ffffff', fontsize=12)
ax.set_title(f"WatchdogAI Performance Accuracy ({accuracy:.1f}%)", color='#00E620', fontsize=14, fontweight='bold')
ax.tick_params(colors='#ffffff', labelsize=11)
ax.spines['bottom'].set_color('#ffffff')
ax.spines['left'].set_color('#ffffff')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(facecolor='#000000', edgecolor='#ffffff', labelcolor='#ffffff')

plt.tight_layout()
plt.savefig("accuracy_chart.png", dpi=300, facecolor='#000000', edgecolor='none')
print("📊 Performance chart successfully saved as 'accuracy_chart.png'!")
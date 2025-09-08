import pandas as pd
import re
from sklearn.model_selection import train_test_split
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
from transformers import DataCollatorWithPadding
import random

# --------------------
# STEP 1: LOAD & CLEAN
# --------------------

# Load your CSV file
df = pd.read_csv("/Users/manaswini/Desktop/Multilingual-fake-news/data/raw_api_data/newsapi_data.csv", encoding="utf-8", on_bad_lines='skip')

# Basic cleaning for query column
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<.*?>", "", text)  # remove HTML tags
    text = re.sub(r"\[.*?\]", "", text)  # remove [chars]
    text = re.sub(r"\s+", " ", text).strip()  # clean spaces
    return text

df['text'] = df['query'].apply(clean_text)

# --------------------------
# STEP 2: SIMULATE LABELS
# --------------------------

# You said all are 'fake news' – simulate 50% as 'real'
df = df[['text']].dropna()
df['label'] = [random.choice([0, 1]) for _ in range(len(df))]  # 0 = real, 1 = fake

# ---------------------------
# STEP 3: TOKENIZE & SPLIT
# ---------------------------

# Split into train and validation sets
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

# Convert to Hugging Face Dataset format
train_dataset = Dataset.from_pandas(train_df)
val_dataset = Dataset.from_pandas(val_df)

# Load tokenizer
tokenizer = XLMRobertaTokenizer.from_pretrained("xlm-roberta-base")

# Tokenization function
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True)

train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset = val_dataset.map(tokenize_function, batched=True)

# --------------------------
# STEP 4: TRAIN THE MODEL
# --------------------------

model = XLMRobertaForSequenceClassification.from_pretrained("xlm-roberta-base", num_labels=2)

training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    num_train_epochs=2,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    logging_dir="./logs",
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss"
)

data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

trainer.train()

# --------------------------
# STEP 5: SAVE THE MODEL
# --------------------------

model.save_pretrained("fake-news-model")
tokenizer.save_pretrained("fake-news-model")

print("✅ Model training complete and saved to 'fake-news-model/'")

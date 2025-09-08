# Databricks notebook source
import pandas as pd
import re

# Your nested JSON data
data = [
    {
        "question": "1",
        "sub_topics": [
            {
                "topic": "Synthetic Data Generation",
                "sub_questions": [
                    {"sub_question": "1.1", "text": "Does your platform support synthetic data generation?"},
                    {"sub_question": "1.2", "text": "How is synthetic data generation supported in your platform?"},
                    {"sub_question": "1.3", "text": "Please provide any further detail on how synthetic data generation is supported. (Maximum 1000 characters)"}
                ]
            },
            {
                "topic": "AI-Based Recommendation",
                "sub_questions": [
                    {"sub_question": "1.4", "text": "Does your platform support AI-based recommendations?"},
                    {"sub_question": "1.5", "text": "How are AI-based recommendations supported in your platform?"},
                    {"sub_question": "1.6", "text": "Please provide any further detail on how AI-based recommendations are supported. (Maximum 1000 characters)"}
                ]
            }
        ]
    },
    {
        "question": "2",
        "sub_topics": [
            {
                "topic": "Data Augmentation",
                "sub_questions": [
                    {"sub_question": "2.1", "text": "Does your platform support data augmentation?"},
                    {"sub_question": "2.2", "text": "How is data augmentation supported in your platform?"},
                    {"sub_question": "2.3", "text": "Please provide any further detail on how data augmentation is supported. (Maximum 1000 characters)"}
                ]
            }
        ]
    }
]

# 1. Flatten the JSON using json_normalize
df = pd.json_normalize(
    data,
    record_path=['sub_topics', 'sub_questions'],
    meta=['question', ['sub_topics', 'topic']],
    errors='ignore'
)

# 2. Rename columns for clarity
df = df.rename(columns={
    'sub_question': 'sub_question_id',
    'text': 'question_text',
    'sub_topics.topic': 'topic',
    'question': 'question_id'
})

# 3. Create a single rendered question string
df['rendered_q'] = df['sub_question_id'] + ": " + df['question_text']
df

# COMMAND ----------


# 4. Group by topic, preserving question_id and concatenating rendered questions
grouped = (
    df.groupby('topic', as_index=False)
      .agg(
          question_id=('question_id', 'first'),
          sub_question_ids=('sub_question_id', list),
          concatenated_questions=('rendered_q', '\n\n'.join)
      )
)

grouped

# COMMAND ----------

import pandas as pd
import re

# Your nested JSON data
data = [
    {
        "question": "2",
        "sub_topics": [
            {
                "topic": "Data Augmentation",
                "sub_questions": [
                    {"sub_question": "2.1", "text": "Does your platform support data augmentation?"},
                    {"sub_question": "2.2", "text": "How is data augmentation supported in your platform?"},
                    {"sub_question": "2.3", "text": "Please provide any further detail on how data augmentation is supported. (Maximum 1000 characters)"}
                ]
            }
        ]
    }
]

# 1. Flatten the JSON using json_normalize
df = pd.json_normalize(
    data,
    record_path=['sub_topics', 'sub_questions'],
    meta=['question', ['sub_topics', 'topic']],
    errors='ignore'
)

# 2. Rename columns for clarity
df = df.rename(columns={
    'sub_question': 'sub_question_id',
    'text': 'question_text',
    'sub_topics.topic': 'topic',
    'question': 'question_id'
})

# 3. Create a single rendered question string
df['rendered_q'] = df['sub_question_id'] + ": " + df['question_text']
df

# 4. Group by topic, preserving question_id and concatenating rendered questions
grouped = (
    df.groupby('topic', as_index=False)
      .agg(
          question_id=('question_id', 'first'),
          sub_question_ids=('sub_question_id', list),
          concatenated_questions=('rendered_q', '\n\n'.join)
      )
)

grouped
# Example LLM JSON response
json_response = {
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": """2.1: Yes, Databricks provides several techniques to augment training data to improve the performance of ML models, via built-in libraries & via 3rd-party integrations.

2.2: Included as open source library components in your core DSML platform offering

2.3: The Databricks ML Runtime includes built-in tools such as TorchVision's augmentation tools & TensorFlow's preprocessing tools for data augmentation across various modalities. Users can also import & use custom data augmentation tools, such as Snorkel, to artificially expand their training datasets. This capability is particularly valuable for improving model performance in scenarios w/ limited data. Additionally, Databricks supports third-party integrations like Informatica for more advanced data augmentation needs. The platform's flexibility allows data scientists to implement domain-specific augmentation techniques tailored to their unique use cases, whether working w/ images, text, tabular data, or other modalities."""
      },
      "finish_reason": "stop"
    }
  ],
  "id": "5509ae9c-f9ad-49b3-8d19-49546c473df1"
}

# 1. Extract the assistant's content
content = json_response["choices"][0]["message"]["content"]

# 2. Parse with regex: capture ID and answer text (DOTALL so answers can span lines)
pattern = r'(\d+\.\d+):\s*(.*?)(?=\n\n\d+\.\d+:|\Z)'
matches = re.findall(pattern, content, flags=re.DOTALL)

# 3. Build a small answers dataframe
answers_df = pd.DataFrame(matches, columns=['sub_question_id', 'answer']).assign(answer=lambda d: d['answer'].str.strip())

# 4. Join back to the original dataframe on sub_question_id
df_with_answers = df.merge(answers_df, on='sub_question_id', how='left')

# Now df_with_answers contains a new 'answer' column aligned by sub-question ID
df_with_answers

# COMMAND ----------


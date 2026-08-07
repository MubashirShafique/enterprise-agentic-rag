
#  Environment Variables Setup

This guide provides a complete walkthrough for setting up all required environment variables and API keys for this project.

---

#  Complete `.env` Template
Create a file named `.env` in the root directory of your project and paste the following:

```env
# Qdrant Vector Database
QDRANT_API_KEY=""
QDRANT_CLUSTER_ENDPOINT=""

# Portkey Gateway
PORTKEY_API_KEY=""
PORTKEY_EMBED_CONFIG_ID=""
PORTKEY_CHAT_CONFIG_ID=""

# Default Models
CHAT_MODEL="gpt-4o-mini"
EMBEDDING_MODEL="text-embedding-3-small"

# LangSmith (Tracing & Evaluation)
LANGSMITH_API_KEY=""
LANGSMITH_TRACING=true
LANGSMITH_PROJECT="pydocs-ai"
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"

# OpenAI
OPENAI_API_KEY=""
```

---

#  Step-by-Step API Key Setup Guide

## 1. Qdrant Vector Database

### Step 1 — Create a Qdrant Cloud Account

Visit:

https://cloud.qdrant.io/

Sign up or log in to your account.

---

### Step 2 — Create a Cluster

After logging in:

- Click **Create Cluster**
- Choose your preferred Cloud Provider and Region
- Wait until the cluster becomes active

---

### Step 3 — Copy Cluster Endpoint

Open your cluster.

Navigate to **Overview**.

Copy the **Cluster Endpoint URL**.

Example:

```env
QDRANT_CLUSTER_ENDPOINT="https://xxxxxxxx-xxxx-xxxx-xxxx.aws.cloud.qdrant.io"
```

---

### Step 4 — Create an API Key

Open:

**API Keys**

or directly visit:

https://cloud.qdrant.io/

Select your cluster → **API Keys** → **Create API Key**

Copy the generated key.

```env
QDRANT_API_KEY="your_api_key"
```

---

# 2. OpenAI API

Visit the OpenAI Platform:

https://platform.openai.com/

Login with your account.

---

### Create API Key

Open:

https://platform.openai.com/api-keys

Click

**Create new secret key**

Give it a name.

Copy the generated key.

Add it to your `.env`.

```env
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

---

# 3. LangSmith (Tracing & Evaluation)

Visit:

https://smith.langchain.com/

Login with your LangSmith account.

---

### Generate API Key

Open Settings:

https://smith.langchain.com/settings

Navigate to:

**API Keys**

Click

**Create API Key**

Copy the generated key.

```env
LANGSMITH_API_KEY="lsv2_xxxxxxxxx"
```

---

### Create a Project

Open:

https://smith.langchain.com/projects

Click

**New Project**

Create a project named exactly:

```text
pydocs-ai
```

Update your `.env`

```env
LANGSMITH_PROJECT="pydocs-ai"
```

---

# 4. Portkey AI Gateway

Visit:

https://app.portkey.ai/

Sign up or login.

---

## Step A — Generate Portkey API Key

Open:

https://app.portkey.ai/api-keys

Click

**Create API Key**

Copy it.

```env
PORTKEY_API_KEY="pk_xxxxxxxxx"
```

---

## Step B — Create Virtual Keys

Open:

https://app.portkey.ai/virtual-keys

Create the following Virtual Keys by connecting your provider API keys.

| Virtual Key | Provider |
|-------------|----------|
| pydocs | OpenAI |
| pydocs1 | OpenAI |
| gemini | Google Gemini |
| gemini1 | Google Gemini |
| grok | xAI Grok |
| grok1 | xAI Grok |

Once all Virtual Keys are created, continue to Configurations.

---

## Step C — Create Configurations

Open:

https://app.portkey.ai/configs

Click

**+ Create Config**

Switch to **JSON Mode**.

Paste the JSON configuration shown below.

Save it.

Portkey will generate a **Config ID (Slug)**.

Copy the generated Config IDs.

```env
PORTKEY_CHAT_CONFIG_ID=""
PORTKEY_EMBED_CONFIG_ID=""
```

---

#  Chat Configuration (`PORTKEY_CHAT_CONFIG_ID`)

Paste the following JSON while creating the Chat Configuration.

```json
{
  "strategy": {
    "mode": "fallback"
  },
  "targets": [
    {
      "strategy": {
        "mode": "loadbalance"
      },
      "targets": [
        {
          "virtual_key": "pydocs",
          "weight": 0.5,
          "override_params": {
            "model": "gpt-4o"
          }
        },
        {
          "virtual_key": "pydocs1",
          "weight": 0.5,
          "override_params": {
            "model": "gpt-4o"
          }
        }
      ],
      "retry": {
        "attempts": 3,
        "on_status_codes": [
          429,
          500,
          502,
          503,
          504
        ]
      }
    },
    {
      "strategy": {
        "mode": "loadbalance"
      },
      "targets": [
        {
          "virtual_key": "gemini",
          "weight": 0.5,
          "override_params": {
            "model": "gemini-2.5-pro"
          }
        },
        {
          "virtual_key": "gemini1",
          "weight": 0.5,
          "override_params": {
            "model": "gemini-2.5-pro"
          }
        }
      ],
      "retry": {
        "attempts": 3,
        "on_status_codes": [
          429,
          500,
          502,
          503,
          504
        ]
      }
    },
    {
      "strategy": {
        "mode": "loadbalance"
      },
      "targets": [
        {
          "virtual_key": "grok",
          "weight": 0.5,
          "override_params": {
            "model": "grok-4"
          }
        },
        {
          "virtual_key": "grok1",
          "weight": 0.5,
          "override_params": {
            "model": "grok-4"
          }
        }
      ],
      "retry": {
        "attempts": 3,
        "on_status_codes": [
          429,
          500,
          502,
          503,
          504
        ]
      }
    }
  ],
  "cache": {
    "mode": "simple"
  },
  "request_timeout": 30000
}
```

---

#⚙️ Embedding Configuration (`PORTKEY_EMBED_CONFIG_ID`)

Paste the following JSON while creating the Embedding Configuration.

```json
{
  "strategy": {
    "mode": "loadbalance"
  },
  "targets": [
    {
      "virtual_key": "pydocs",
      "weight": 0.5,
      "override_params": {
        "model": "text-embedding-3-small"
      }
    },
    {
      "virtual_key": "pydocs1",
      "weight": 0.5,
      "override_params": {
        "model": "text-embedding-3-small"
      }
    }
  ],
  "retry": {
    "attempts": 3,
    "on_status_codes": [
      429,
      500,
      502,
      503,
      504
    ]
  },
  "cache": {
    "mode": "simple"
  },
  "request_timeout": 15000
}
```

---

# ✅ Final Checklist

Before running the project, make sure you have completed all of the following:

- ✅ Created a Qdrant Cloud cluster
- ✅ Copied the Qdrant Cluster Endpoint
- ✅ Generated a Qdrant API Key
- ✅ Generated an OpenAI API Key
- ✅ Generated a LangSmith API Key
- ✅ Created the `pydocs-ai` project in LangSmith
- ✅ Generated a Portkey API Key
- ✅ Created all required Portkey Virtual Keys
- ✅ Created the Chat Configuration
- ✅ Created the Embedding Configuration
- ✅ Added every value to your `.env` file

Once all environment variables are configured correctly, you are ready to run the project.


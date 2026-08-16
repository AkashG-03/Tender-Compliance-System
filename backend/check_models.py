from openai import OpenAI
from dotenv import load_dotenv

# Load .env so OPENAI_API_KEY is available
load_dotenv()

client = OpenAI()  # will read OPENAI_API_KEY from env

def main():
    try:
        print("🔑 Checking models available for this API key...\n")
        models = client.models.list()

        print("✅ Models you can use:\n")
        for i, m in enumerate(models.data[:30], start=1):
            print(f"{i:02d}. {m.id}")

        if len(models.data) > 30:
            print(f"\n... and {len(models.data) - 30} more")

    except Exception as e:
        print("\n❌ Error while listing models:")
        print(type(e).__name__, ":", e)

if __name__ == "__main__":
    main()

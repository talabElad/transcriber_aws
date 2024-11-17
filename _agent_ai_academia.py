import boto3
import json
import os
#from dotenv import load_dotenv


def ai_agent_clean(prompt):
    # Load environment variables
    #load_dotenv()

    # Set up Amazon Bedrock client
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    # Configure the model
    model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

    # Define the system prompt
    system_prompt = """
אתה אפליקציית תמלול מקצועית. קיבלת קטע טקסט ותפקידך לבצע את המשימות הבאות:

ניקוי שגיאות: נקה את הטקסט משגיאות כתיב, טעויות דקדוקיות ומילים חוזרות. ודא שהמשפטים זורמים בצורה טבעית.
הוספת סימני פיסוק: הוסף סימני פיסוק מתאימים (כגון פסיקים, נקודות, סימני שאלה וקריאה) בכל מקום שנדרש, על מנת לשפר את הקריאות.
המרת מספרים ותאריכים: המרה של מספרים (למשל, "שמונה" ל-8), תאריכים (למשל, "חמישה בספטמבר אלפיים עשרים ושלוש" ל-5.9.2023), וזמנים (למשל, "שתיים וחצי" ל-2:30), אם ישנם כאלו בטקסט.
דוגמה: טקסט קלט: "היום יש לי פגישה בשעה שתיים וחצי אחרי הצהריים. אני מקווה שהיא תסתיים עד ארבע וחצי." תוצאה מבוקשת: "היום יש לי פגישה בשעה 2:30 אחרי הצהריים. אני מקווה שהיא תסתיים עד 4:30."
        """

    # Prepare the request body
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": system_prompt + "\n" + prompt}]
            }
        ],
    }

    # Invoke the model
    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
        )

        # Parse the response
        result = json.loads(response["body"].read())

        # Extract and return the content
        return result['content'][0]['text']

    except Exception as e:
        return f"An error occurred: {str(e)}"


def ai_agent_summary(prompt):
    # Load environment variables
    #load_dotenv()

    # Set up Amazon Bedrock client
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    # Configure the model
    model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

    # Define the system prompt
    system_prompt = """
   ההקלטה הינה של מידע הניתן על קורס באוניברסיטה, תסכם בבקשה את המידע ותוסיף שאלות נוספות שיהיה לסטונדט מעניין לשאול על הקורס לפני שהוא לוקח אותו
        """

    # Prepare the request body
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": system_prompt + "\n" + prompt}]
            }
        ],
    }

    # Invoke the model
    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
        )

        # Parse the response
        result = json.loads(response["body"].read())

        # Extract and return the content
        return result['content'][0]['text']

    except Exception as e:
        return f"An error occurred: {str(e)}"




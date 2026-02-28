import pandas as pd
import json
import re

def clean_text(text):
    """Sanitize text by removing non-printable characters and extra whitespace"""
    if pd.isna(text) or text == "" or text == 0:
        return None
    text = str(text)
    text = re.sub(r'[\n\r\t]', ' ', text)
    text = ' '.join(text.split())
    return text.strip()

def classify_lead(source_value, mapping_rules, default_role):
    """Classify lead based on source value using mapping table"""
    cleaned = clean_text(source_value)
    if cleaned is None:
        return default_role
    return mapping_rules.get(cleaned, default_role)

def main():
    # Define mapping rules directly for standalone execution
    mapping_rules = {
        "Buyer_Line": "BUYER",
        "Partner_Line": "CHANNEL_PARTNER",
        "Visit_Line": "SITE_VISIT",
        "Buyer": "BUYER",
        "Channel Partner": "CHANNEL_PARTNER",
        "Site Visit": "SITE_VISIT"
    }
    default_role = "UNKNOWN"
    
    # Load leads
    # Using the file provided in context
    df = pd.read_csv('data/leads_1000.csv') 
    
    # Apply classification
    df['Role'] = df['Buyer/Channel Partner/Enquiry/Site Visit'].apply(
        lambda x: classify_lead(x, mapping_rules, default_role)
    )
    
    # Save classified leads
    df.to_csv('data/classified_leads.csv', index=False)
    
    # Print statistics
    print("Classification Complete!")
    print("\nRole Distribution:")
    print(df['Role'].value_counts())
    print(f"\nTotal Leads: {len(df)}")
    
    return df

if __name__ == "__main__":
    main()

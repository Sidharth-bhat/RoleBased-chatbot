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
    # Load mapping table
    with open('classification/mapping_table.json', 'r') as f:
        config = json.load(f)
    
    mapping_rules = config['mapping_rules']
    default_role = config['default_role']
    
    # Load leads
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

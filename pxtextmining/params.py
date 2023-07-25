dataset = "datasets/hidden/multilabel_230719.csv"

random_state = 42

model_name = "distilbert-base-uncased"

q_map = {
    "Please tell us why": "nonspecific",
    "Please tells us why you gave this answer?": "nonspecific",
    "FFT Why?": "nonspecific",
    "What was good?": "what_good",
    "Is there anything we could have done better?": "could_improve",
    "How could we improve?": "could_improve",
    "What could we do better?": "could_improve",
    "Please can you tell us why you gave your answer and what we could have done better?": "nonspecific",
    "Please describe any things about the 111 service that\r\nyou were particularly satisfied and/or dissatisfied with": "nonspecific",
    "Please describe any things about the 111 service that \nyou were particularly satisfied and/or dissatisfied with": "nonspecific",
    "Please describe any things about the 111 service that\nyou were particularly satisfied and/or dissatisfied with": "nonspecific",
    "Nonspecific": "nonspecific",
    "nonspecific": "nonspecific",
}

# v6
major_cat_dict = {
    "General": [
        "Labelling not possible",
        "Positive experience & gratitude",
        "Negative experience & dissatisfaction",
        "Not assigned",
        "Organisation & efficiency",
        "Funding & use of financial resources",
    ],
    "Staff": [
        "Staff manner & personal attributes",
        "Number & deployment of staff",
        "Staff responsiveness",
        "Staff continuity",
        "Competence & training",
    ],
    "Communication & involvement": [
        "Unspecified communication",
        "Staff listening, understanding & involving patients",
        "Information directly from staff during care",
        "Information provision & guidance",
        "Being kept informed, clarity & consistency of information",
        "Interaction with family/ carers",
    ],
    "Access to medical care & support": [
        "Contacting services",
        "Appointment arrangements",
        "Appointment method",
        "Timeliness of care",
    ],
    "Medication": ["Supplying & understanding medication", "Pain management"],
    "Patient journey & service coordination": [
        "Diagnosis & triage",
        "Referals & continuity of care",
        "Admission",
        "Discharge",
        "Care plans",
        "Patient records",
        "Impact of treatment/ care",
    ],
    "Food & diet": ["Food & drink provision & facilities"],
    "Category TBC": [
        "Feeling safe",
        "Patient appearance & grooming",
        "Equality, Diversity & Inclusion",
    ],
    "Activities": ["Activities & access to fresh air", "Electronic entertainment"],
    "Environment & equipment": [
        "Cleanliness, tidiness & infection control",
        "Sensory experience",
        "Environment & Facilities",
        "Provision of medical equipment",
    ],
    "Mental Health specifics": ["Mental Health Act"],
    "Service location, travel & transport": [
        "Service location",
        "Transport to/ from services",
        "Parking",
    ],
}

major_cats = list(major_cat_dict.keys())

# v6 20230602
merged_minor_cats = [
    "Gratitude/ good experience",
    #     "Negative experience",
    "Not assigned",
    "Organisation & efficiency",
    #     "Funding & use of financial resources",
    "Non-specific praise for staff",
    #     "Non-specific dissatisfaction with staff",
    "Staff manner & personal attributes",
    "Number & deployment of staff",
    "Staff responsiveness",
    "Staff continuity",
    "Competence & training",
    "Unspecified communication",
    "Staff listening, understanding & involving patients",
    "Information directly from staff during care",
    "Information provision & guidance",
    "Being kept informed, clarity & consistency of information",
    #     "Service involvement with family/ carers",
    #     "Patient contact with family/ carers",
    "Contacting services",
    "Appointment arrangements",
    "Appointment method",
    "Timeliness of care",
    "Pain management",
    "Diagnosis & triage",
    "Referals & continuity of care",
    #     "Length of stay/ duration of care",
    "Discharge",
    "Care plans",
    #     "Patient records",
    #     "Links with non-NHS organisations",
    "Cleanliness, tidiness & infection control",
    "Safety & security",
    #     "Provision of medical equipment",
    "Service location",
    "Transport to/ from services",
    "Parking",
    "Electronic entertainment",
    "Feeling safe",
    "Patient appearance & grooming",
    "Mental Health Act",
    "Equality, Diversity & Inclusion",
    "Admission",
    #     "Collecting patients feedback",
    "Labelling not possible",
    "Environment & Facilities",
    "Supplying & understanding medication",
    "Activities & access to fresh air",
    "Food & drink provision & facilities",
    "Sensory experience",
    "Impact of treatment/ care",
    "Negative experience/ dissatisfaction",
    "Family/ carers",
]

# v6 20230806
minor_cats = [
    "Not assigned",
    "Organisation & efficiency",
    "Funding & use of financial resources",
    "Staff manner & personal attributes",
    "Number & deployment of staff",
    "Staff responsiveness",
    "Staff continuity",
    "Competence & training",
    "Unspecified communication",
    "Staff listening, understanding & involving patients",
    "Information directly from staff during care",
    "Information provision & guidance",
    "Being kept informed, clarity & consistency of information",
    "Contacting services",
    "Appointment arrangements",
    "Appointment method",
    "Timeliness of care",
    "Pain management",
    "Diagnosis & triage",
    "Referals & continuity of care",
    "Discharge",
    "Care plans",
    "Patient records",
    "Cleanliness, tidiness & infection control",
    "Provision of medical equipment",
    "Service location",
    "Transport to/ from services",
    "Parking",
    "Electronic entertainment",
    "Feeling safe",
    "Patient appearance & grooming",
    "Mental Health Act",
    "Equality, Diversity & Inclusion",
    "Admission",
    "Labelling not possible",
    "Environment & Facilities",
    "Supplying & understanding medication",
    "Activities & access to fresh air",
    "Food & drink provision & facilities",
    "Sensory experience",
    "Impact of treatment/ care",
    # "Psychological therapy arrangements",
    # "Existence of services",
    # "Choice of services",
    # "Out of hours support (community services)",
    # "Learning organisation",
    "Interaction with family/ carers",
    "Negative experience & dissatisfaction",
    "Positive experience & gratitude",
]

sentiment_dict = {
    1: "very positive",
    2: "positive",
    3: "neutral",
    4: "negative",
    5: "very negative",
}

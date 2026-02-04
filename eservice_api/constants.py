PARTNER_FIELDS = [
    "name",
    "email",
    "phone",
    "street",
    "city",
    "state_id",
    "country_id",
]


def get_cleaned_create_values(fields_list=[], json_data={}):
    """Clean up values coming from the other system"""
    cleaned_data = {}
    for field in json_data:
        if field in fields_list:
            cleaned_data[field] = json_data[field]
    return cleaned_data

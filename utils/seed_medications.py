from database.mongo import medication_dictionary
from database.schema.medication_dictionary import MedicationDictionary

async def seed_medication_dictionary():
    """Seed the medication dictionary with common IVF medications."""
    
    common_medications = [
        {
            "name": "Estradiol",
            "common_dosages": ["0.5 mg", "1 mg", "2 mg", "4 mg", "6 mg", "8 mg"],
            "category": "Estrogen",
            "description": "Estrogen medication used in IVF protocols for follicle development"
        },
        {
            "name": "Progesterone",
            "common_dosages": ["25 mg", "50 mg", "100 mg", "200 mg"],
            "category": "Progesterone",
            "description": "Progesterone support after ovulation and during early pregnancy"
        },
        {
            "name": "Gonal-F",
            "common_dosages": ["75 IU", "150 IU", "225 IU", "300 IU", "450 IU"],
            "category": "Gonadotropin",
            "description": "Recombinant FSH for ovarian stimulation"
        },
        {
            "name": "Menopur",
            "common_dosages": ["75 IU", "150 IU", "225 IU"],
            "category": "Gonadotropin",
            "description": "Combined FSH and LH for ovarian stimulation"
        },
        {
            "name": "Cetrotide",
            "common_dosages": ["0.25 mg"],
            "category": "GnRH Antagonist",
            "description": "Prevents premature ovulation during stimulation"
        },
        {
            "name": "Lupron",
            "common_dosages": ["0.1 mg", "0.2 mg", "0.5 mg", "1 mg"],
            "category": "GnRH Agonist",
            "description": "Suppresses natural hormone production"
        },
        {
            "name": "Pregnyl",
            "common_dosages": ["5,000 IU", "10,000 IU"],
            "category": "hCG",
            "description": "Triggers ovulation after stimulation"
        },
        {
            "name": "Endometrin",
            "common_dosages": ["100 mg"],
            "category": "Progesterone",
            "description": "Vaginal progesterone support"
        },
        {
            "name": "Crinoane",
            "common_dosages": ["8%", "10%"],
            "category": "Progesterone",
            "description": "Vaginal progesterone gel"
        },
        {
            "name": "Baby Aspirin",
            "common_dosages": ["81 mg"],
            "category": "Blood Thinner",
            "description": "Low-dose aspirin for blood flow improvement"
        }
    ]
    
    for med_data in common_medications:
        # Check if medication already exists
        existing = await medication_dictionary.find_one({"name": med_data["name"]})
        if not existing:
            medication = MedicationDictionary(**med_data)
            await medication_dictionary.insert_one(medication.dict(by_alias=True))
            print(f"Added medication: {med_data['name']}")
        else:
            print(f"Medication already exists: {med_data['name']}")

# Run this function during app startup or as a management command
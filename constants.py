from frozendict import frozendict

starting_buildings = frozendict(
    {
        "wheat_field": (1, 0),
        "bakery": (1, 0),
    }
)

building_cost: frozendict = frozendict(
    {
        "wheat_field": 1,
        "apple_orchard": 3,
        "ranch": 1,
        "forest": 3,
        "mine": 6,
        "fruit_and_vegetable_market": 2,
        "cheese_factory": 5,
        "furniture_factory": 3,
        "bakery": 1,
        "convenience_store": 2,
        "cafe": 2,
        "family_restaurant": 3,
        "stadium": 6,
        "tv_station": 7,
        "business_center": 8,
        "shopping_mall": 10,
        "amusement_park": 16,
        "radio_tower": 22,
        "airport": 30,
        "train_station": 4,
        "flower_garden": 2,
        "mackerel_boat": 2,
        "tuna_boat": 5,
        "flower_shop": 1,
        "food_warehouse": 2,
        "sushi_bar": 2,
        "pizza_joint": 1,
        "hamburger_stand": 1,
        "publisher": 5,
        "tax_office": 4,
        "harbor": 2,
    }
)

activation_dict = frozendict(
    {
        "wheat_field": {"roll": (1,), "value": 1},
        "apple_orchard": {"roll": (10,), "value": 3},
        "ranch": {"roll": (2,), "value": 1},
        "forest": {"roll": (5,), "value": 1},
        "mine": {"roll": (9,), "value": 5},
        "fruit_and_vegetable_market": {"roll": (11, 12), "value": "special"},
        "cheese_factory": {"roll": (7,), "value": "special"},
        "furniture_factory": {"roll": (8,), "value": "special"},
        "bakery": {"roll": (2, 3), "value": 1},
        "convenience_store": {"roll": (4,), "value": 3},
        "cafe": {"roll": (3,), "value": 1},
        "family_restaurant": {"roll": (9, 10), "value": 2},
        "stadium": {"roll": (6,), "value": "special"},
        "tv_station": {"roll": (6,), "value": "special"},
        "business_center": {"roll": (6,), "value": "special"},
        "flower_garden": {"roll": (4,), "value": 1},
        "mackerel_boat": {"roll": (8,), "value": 3},
        "tuna_boat": {"roll": (12, 13, 14), "value": "special"},
        "flower_shop": {"roll": (6,), "value": "special"},
        "food_warehouse": {"roll": (12, 13), "value": "special"},
        "sushi_bar": {"roll": (1,), "value": "special"},
        "pizza_joint": {"roll": (7,), "value": 1},
        "hamburger_stand": {"roll": (8,), "value": 1},
        "publisher": {"roll": (7,), "value": "special"},
        "tax_office": {"roll": (8, 9), "value": "special"},

    }
)

landmarks_tuple = (
    "train_station",
    "shopping_mall",
    "amusement_park",
    "radio_tower",
    "harbor",
    "airport",
)

major_establishments_tuple = (
    "stadium",
    "tv_station",
    "business_center",
    "publisher",
    "tax_office",
)

primary_industry_dict = frozendict(
    {
        "wheat_field": "wheat",
        "ranch": "cow",
        "forest": "gear",
        "mine": "gear",
        "apple_orchard": "wheat",
        "flower_garden": "wheat",
        "mackerel_boat": "boat",
        "tuna_boat": "boat",
    }
)

secondary_industry_dict = frozendict(
    {
        "bakery": "bread",
        "convenience_store": "bread",
        "cheese_factory": "factory",
        "furniture_factory": "factory",
        "fruit_and_vegetable_market": "fruit",
        "flower_shop": "bread",
        "food_warehouse": "factory",
    }
)

restaurants_tuple = (
    "cafe",
    "family_restaurant",
    "sushi_bar",
    "pizza_joint",
    "hamburger_stand",
)
player_limit = frozendict({})

BUILDING_ORDER = sorted(building_cost.keys())

BUILDING_INDEX = {key: i for i, key in enumerate(BUILDING_ORDER)}

# need to make sure vector is consistent
BUILDING_VECTOR_TEMPLATE = [[0 for _ in range(player_limit[key] + 1)] for key in BUILDING_ORDER]

SWAPPABLE_BUILDING_ORDER = [building for building in BUILDING_ORDER if building not in
                            ('stadium', 'tv_station', 'business_center', 'shopping_mall', 'station', 'amusement_park',
                             'radio_tower', 'airport', 'harbor', 'tax_office', 'publisher')]

SWAPPABLE_BUILDING_INDEX = {key: i for i, key in enumerate(SWAPPABLE_BUILDING_ORDER)}

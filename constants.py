from frozendict import frozendict
from Building import Building
from BuildingType import BuildingType

starting_buildings = {
    Building.WHEAT_FIELD: 1,
    Building.BAKERY: 1
}

building_cost: dict[Building, int] = {
    Building.WHEAT_FIELD: 1,
    Building.APPLE_ORCHARD: 3,
    Building.RANCH: 1,
    Building.FOREST: 3,
    Building.MINE: 6,
    Building.FRUIT_AND_VEGETABLE_MARKET: 2,
    Building.CHEESE_FACTORY: 5,
    Building.FURNITURE_FACTORY: 3,
    Building.BAKERY: 1,
    Building.CONVENIENCE_STORE: 2,
    Building.CAFE: 2,
    Building.FAMILY_RESTAURANT: 3,
    Building.STADIUM: 6,
    Building.TV_STATION: 7,
    Building.BUSINESS_CENTER: 8,
    Building.SHOPPING_MALL: 10,
    Building.AMUSEMENT_PARK: 16,
    Building.RADIO_TOWER: 22,
    Building.AIRPORT: 30,
    Building.TRAIN_STATION: 4,
    Building.FLOWER_GARDEN: 2,
    Building.MACKEREL_BOAT: 2,
    Building.TUNA_BOAT: 5,
    Building.FLOWER_SHOP: 1,
    Building.FOOD_WAREHOUSE: 2,
    Building.SUSHI_BAR: 2,
    Building.PIZZA_JOINT: 1,
    Building.HAMBURGER_STAND: 1,
    Building.PUBLISHER: 5,
    Building.TAX_OFFICE: 4,
    Building.HARBOR: 2
}
activation_dict = frozendict(
    {
        Building.WHEAT_FIELD: {"roll": (1,), "value": 1},
        Building.APPLE_ORCHARD: {"roll": (10,), "value": 3},
        Building.RANCH: {"roll": (2,), "value": 1},
        Building.FOREST: {"roll": (5,), "value": 1},
        Building.MINE: {"roll": (9,), "value": 5},
        Building.FRUIT_AND_VEGETABLE_MARKET: {"roll": (11, 12), "value": "special"},
        Building.CHEESE_FACTORY: {"roll": (7,), "value": "special"},
        Building.FURNITURE_FACTORY: {"roll": (8,), "value": "special"},
        Building.BAKERY: {"roll": (2, 3), "value": 1},
        Building.CONVENIENCE_STORE: {"roll": (4,), "value": 3},
        Building.CAFE: {"roll": (3,), "value": 1},
        Building.FAMILY_RESTAURANT: {"roll": (9, 10), "value": 2},
        Building.STADIUM: {"roll": (6,), "value": "special"},
        Building.TV_STATION: {"roll": (6,), "value": "special"},
        Building.BUSINESS_CENTER: {"roll": (6,), "value": "special"},
        Building.FLOWER_GARDEN: {"roll": (4,), "value": 1},
        Building.MACKEREL_BOAT: {"roll": (8,), "value": 3},
        Building.TUNA_BOAT: {"roll": (12, 13, 14), "value": "special"},
        Building.FLOWER_SHOP: {"roll": (6,), "value": "special"},
        Building.FOOD_WAREHOUSE: {"roll": (12, 13), "value": "special"},
        Building.SUSHI_BAR: {"roll": (1,), "value": "special"},
        Building.PIZZA_JOINT: {"roll": (7,), "value": 1},
        Building.HAMBURGER_STAND: {"roll": (8,), "value": 1},
        Building.PUBLISHER: {"roll": (7,), "value": "special"},
        Building.TAX_OFFICE: {"roll": (8, 9), "value": "special"},

    }
)

landmarks_tuple = (
    Building.TRAIN_STATION,
    Building.SHOPPING_MALL,
    Building.AMUSEMENT_PARK,
    Building.RADIO_TOWER,
    Building.HARBOR,
    Building.AIRPORT,
)

major_establishments_tuple = (
    Building.STADIUM,
    Building.TV_STATION,
    Building.BUSINESS_CENTER,
    Building.PUBLISHER,
    Building.TAX_OFFICE,
)

primary_industry_dict = frozendict(
    {
        Building.WHEAT_FIELD: BuildingType.WHEAT,
        Building.RANCH: BuildingType.COW,
        Building.FOREST: BuildingType.GEAR,
        Building.MINE: BuildingType.GEAR,
        Building.APPLE_ORCHARD: BuildingType.WHEAT,
        Building.FLOWER_GARDEN: BuildingType.WHEAT,
        Building.MACKEREL_BOAT: BuildingType.BOAT,
        Building.TUNA_BOAT: BuildingType.BOAT,
    }
)

secondary_industry_dict = frozendict(
    {
        Building.BAKERY: BuildingType.BREAD,
        Building.CONVENIENCE_STORE: BuildingType.BREAD,
        Building.CHEESE_FACTORY: BuildingType.FACTORY,
        Building.FURNITURE_FACTORY: BuildingType.FACTORY,
        Building.FRUIT_AND_VEGETABLE_MARKET: BuildingType.FRUIT,
        Building.FLOWER_SHOP: BuildingType.BREAD,
        Building.FOOD_WAREHOUSE: BuildingType.FACTORY,
    }
)

restaurants_tuple = (
    Building.CAFE,
    Building.FAMILY_RESTAURANT,
    Building.SUSHI_BAR,
    Building.PIZZA_JOINT,
    Building.HAMBURGER_STAND,
)

player_limit = {landmark: 1 for landmark in landmarks_tuple}
player_limit = {
    **player_limit,
    **{
        major_establishment: 1
        for major_establishment in major_establishments_tuple
    },
}
for building in (
        list(primary_industry_dict.keys())
        + list(secondary_industry_dict.keys())
        + list(restaurants_tuple)
):
    player_limit[building] = 6

# need to make sure vector is consistent
# BUILDING_VECTOR_TEMPLATE = [[0 for _ in range(player_limit[key] + 1)] for key in Building]

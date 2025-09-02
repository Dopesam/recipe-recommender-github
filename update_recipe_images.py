#!/usr/bin/env python3

import sqlite3
import os

# Database path
DB_PATH = os.path.join('database', 'recipes.db')

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Updated image mappings for specific foods
recipe_image_updates = {
    # Kenyan Traditional
    1: 'https://images.unsplash.com/photo-1633449156253-3b135da9e02b?w=400&h=300&fit=crop',  # Ugali - corn meal
    2: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=300&fit=crop',  # Nyama Choma - grilled meat
    3: 'https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?w=400&h=300&fit=crop',  # Sukuma Wiki - collard greens
    4: 'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&h=300&fit=crop',  # Githeri - beans and corn
    5: 'https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=400&h=300&fit=crop',  # Mandazi - fried bread
    6: 'https://images.unsplash.com/photo-1574483254805-a3b09e693d45?w=400&h=300&fit=crop',  # Chapati - flatbread
    7: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop',  # Pilau - spiced rice
    8: 'https://images.unsplash.com/photo-1601050690117-94f5f6fa44d4?w=400&h=300&fit=crop',  # Samosas - triangular pastries
    9: 'https://images.unsplash.com/photo-1506802913710-40e2e66339c9?w=400&h=300&fit=crop',  # Kachumbari - tomato salad
    10: 'https://images.unsplash.com/photo-1606491956391-491887847f97?w=400&h=300&fit=crop', # Mukimo - mashed vegetables
    11: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Fish Stew - fish curry
    12: 'https://images.unsplash.com/photo-1606491956391-491887847f97?w=400&h=300&fit=crop', # Irio - mashed potatoes with peas
    13: 'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&h=300&fit=crop', # Maharagwe - kidney beans
    14: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Mutura - sausage
    15: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=300&fit=crop', # Matoke - green bananas
    16: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Bhajia - potato fritters
    17: 'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&h=300&fit=crop', # Kunde - black-eyed peas
    18: 'https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=400&h=300&fit=crop', # Maandazi - sweet fried bread
    19: 'https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?w=400&h=300&fit=crop', # Terere - amaranth greens
    20: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Viazi Karai - spiced potatoes
    21: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop', # Wali wa Nazi - coconut rice
    22: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Smokies - grilled sausages
    23: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop', # Chai - Kenyan tea
    
    # West African
    24: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # Egusi Soup
    25: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=300&fit=crop', # Kelewele - fried plantain
    26: 'https://images.unsplash.com/photo-1633449156253-3b135da9e02b?w=400&h=300&fit=crop', # Banku - fermented corn dough
    27: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # Moi Moi - bean pudding
    28: 'https://images.unsplash.com/photo-1633449156253-3b135da9e02b?w=400&h=300&fit=crop', # Plantain Fufu
    29: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop', # Jollof Rice
    30: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Tagine - Moroccan stew
    31: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Bobotie - South African mince
    32: 'https://images.unsplash.com/photo-1574483254805-a3b09e693d45?w=400&h=300&fit=crop', # Injera - Ethiopian bread
    33: 'https://images.unsplash.com/photo-1633449156253-3b135da9e02b?w=400&h=300&fit=crop', # Couscous - semolina grain
    34: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Bunny Chow - curry in bread
    35: 'https://images.unsplash.com/photo-1633449156253-3b135da9e02b?w=400&h=300&fit=crop', # Fufu - cassava
    36: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Biltong - dried meat
    37: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Thieboudienne - fish rice
    38: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Doro Wat - Ethiopian chicken stew
    39: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Bunny Suya - grilled meat skewers
    40: 'https://images.unsplash.com/photo-1633449156253-3b135da9e02b?w=400&h=300&fit=crop', # Pap en Vleis - maize porridge
    
    # European
    41: 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop', # Pasta Carbonara
    42: 'https://images.unsplash.com/photo-1534080564583-6be75777b70a?w=400&h=300&fit=crop', # Paella - Spanish rice
    43: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Fish and Chips
    44: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Coq au Vin - French chicken
    45: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Wiener Schnitzel
    46: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Moussaka - Greek casserole
    47: 'https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?w=400&h=300&fit=crop', # Ratatouille - vegetable stew
    
    # Asian
    48: 'https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop', # Pad Thai - Thai noodles
    49: 'https://images.unsplash.com/photo-1579952363873-27d3bfaa0103?w=400&h=300&fit=crop', # Sushi - Japanese
    50: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Butter Chicken - Indian curry
    51: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop', # Fried Rice - Chinese
    52: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # Pho - Vietnamese soup
    53: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # Ramen - Japanese soup
    54: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop', # Biryani - Indian rice
    55: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # Tom Yum Soup - Thai
    
    # American
    56: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=300&fit=crop', # BBQ Ribs
    57: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Tacos
    58: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop', # Hamburger
    59: 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop', # Mac and Cheese
    60: 'https://images.unsplash.com/photo-1562967916-eb82221dfb92?w=400&h=300&fit=crop', # Fried Chicken
    61: 'https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=400&h=300&fit=crop', # Apple Pie
    
    # Middle Eastern
    62: 'https://images.unsplash.com/photo-1571197119282-7c4fe7c2f9f5?w=400&h=300&fit=crop', # Hummus
    63: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=300&fit=crop', # Kebabs
    64: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Falafel
    65: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop', # Pizza Margherita - better pizza image
    66: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Shawarma
    67: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Pierogies
    68: 'https://images.unsplash.com/photo-1555507036-ab794f77c82d?w=400&h=300&fit=crop', # Butter Croissant - better croissant image
    
    # Korean
    69: 'https://images.unsplash.com/photo-1610415946035-bad6d5b9dbb6?w=400&h=300&fit=crop', # Kimchi
    70: 'https://images.unsplash.com/photo-1548940740-204726a19be3?w=400&h=300&fit=crop', # Bulgogi
    71: 'https://images.unsplash.com/photo-1498654896293-37aacf113fd9?w=400&h=300&fit=crop', # Bibimbap
    72: 'https://images.unsplash.com/photo-1562967916-eb82221dfb92?w=400&h=300&fit=crop', # Korean Fried Chicken
    73: 'https://images.unsplash.com/photo-1553621042-f6e147245754?w=400&h=300&fit=crop', # Japchae - glass noodles
    74: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Korean Corn Dog
    75: 'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=300&fit=crop', # Tteokbokki - rice cakes
    76: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop', # Korean Fried Rice
    
    # Brazilian
    77: 'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&h=300&fit=crop', # Feijoada - black bean stew
    78: 'https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=400&h=300&fit=crop', # Brigadeiros - chocolate balls
    79: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Coxinha - chicken croquettes
    80: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Moqueca - fish stew
    81: 'https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=400&h=300&fit=crop', # Pão de Açúcar - dessert
    82: 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400&h=300&fit=crop', # Açaí Bowl - better açaí image
    
    # Vietnamese
    83: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Banh Mi - Vietnamese sandwich
    84: 'https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop', # Fresh Spring Rolls
    85: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # Bun Bo Hue - spicy soup
    86: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop', # Vietnamese Coffee
    
    # More European
    87: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # Bouillabaisse - French fish soup
    88: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # French Onion Soup
    89: 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop', # Crème Brûlée - better dessert image
    90: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Bangers and Mash
    91: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Shepherd's Pie
    92: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Beef Wellington
    93: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Sauerbraten
    94: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Schnitzel
    95: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Beef Stroganoff
    96: 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=300&fit=crop', # Swedish Meatballs
    97: 'https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=400&h=300&fit=crop', # Dutch Pancakes
    98: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Spanish Tortilla
    99: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Goulash
    
    # American Regional
    100: 'https://images.unsplash.com/photo-1609403186715-b8ad3c1f9e8b?w=400&h=300&fit=crop', # New England Clam Chowder
    101: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop', # Jambalaya
    102: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Philly Cheesesteak
    103: 'https://images.unsplash.com/photo-1562967916-eb82221dfb92?w=400&h=300&fit=crop', # Buffalo Wings
    104: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Fish Tacos
    
    # Canadian & Australian
    105: 'https://images.unsplash.com/photo-1606787947584-c6c2d8fa7622?w=400&h=300&fit=crop', # Poutine - fries with gravy
    106: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Tourtière - meat pie
    107: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Australian Meat Pie
    108: 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop', # Pavlova - meringue dessert
    109: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Maple Glazed Salmon
    
    # More Italian
    110: 'https://images.unsplash.com/photo-1596040033229-a21913dfd4b1?w=400&h=300&fit=crop', # Risotto
    111: 'https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&h=300&fit=crop', # Osso Buco
}

# Better food-specific image mappings with more authentic food photography
better_food_images = {
    # Kenyan Traditional - More specific food images
    1: 'https://images.unsplash.com/photo-1603729362193-f4238d4c0267?w=400&h=300&fit=crop',  # Ugali - corn meal dish
    2: 'https://images.unsplash.com/photo-1603039831719-fd6abb98d026?w=400&h=300&fit=crop',  # Nyama Choma - African grilled meat
    3: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',  # Sukuma Wiki - leafy greens
    4: 'https://images.unsplash.com/photo-1583395922949-5ff8fc2f87cf?w=400&h=300&fit=crop',  # Githeri - beans and corn mix
    5: 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop',  # Mandazi - African fried bread
    6: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop',  # Chapati - Indian flatbread
    7: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop',  # Pilau - spiced rice
    8: 'https://images.unsplash.com/photo-1601050690117-94f5f6fa44d4?w=400&h=300&fit=crop',  # Samosas
    9: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop',  # Kachumbari - fresh salad
    10: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Mukimo - mashed vegetables
    11: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Fish Stew
    12: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Irio - mashed potatoes with peas
    13: 'https://images.unsplash.com/photo-1583395922949-5ff8fc2f87cf?w=400&h=300&fit=crop', # Maharagwe - kidney beans
    14: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Mutura - African sausage
    15: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=300&fit=crop', # Matoke - green bananas
    16: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', # Bhajia - potato fritters
    17: 'https://images.unsplash.com/photo-1583395922949-5ff8fc2f87cf?w=400&h=300&fit=crop', # Kunde - black-eyed peas
    18: 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop', # Maandazi - sweet version
    19: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop', # Terere - amaranth greens
    20: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', # Viazi Karai - spiced potatoes
    21: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Wali wa Nazi - coconut rice
    22: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Smokies - grilled sausages
    23: 'https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400&h=300&fit=crop', # Chai - milk tea
    
    # West African with more authentic images
    24: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # Egusi Soup
    25: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', # Kelewele - fried plantain
    26: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Banku - fermented corn
    27: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Moi Moi - bean pudding
    28: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Plantain Fufu
    29: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Jollof Rice
    30: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Tagine
    31: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Bobotie
    32: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', # Injera - Ethiopian bread
    33: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Couscous
    34: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Bunny Chow
    35: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Fufu
    36: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Biltong
    37: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Thieboudienne
    38: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Doro Wat
    39: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Bunny Suya
    40: 'https://images.unsplash.com/photo-1586511925558-a4c6376fe65f?w=400&h=300&fit=crop', # Pap en Vleis
    
    # European dishes with better specific images
    41: 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop', # Pasta Carbonara
    42: 'https://images.unsplash.com/photo-1534080564583-6be75777b70a?w=400&h=300&fit=crop', # Paella
    43: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Fish and Chips
    44: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Coq au Vin
    45: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Wiener Schnitzel
    46: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Moussaka
    47: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop', # Ratatouille
    
    # Asian dishes with specific images
    48: 'https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop', # Pad Thai
    49: 'https://images.unsplash.com/photo-1579952363873-27d3bfaa0103?w=400&h=300&fit=crop', # Sushi
    50: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Butter Chicken
    51: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Fried Rice
    52: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # Pho
    53: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # Ramen
    54: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Biryani
    55: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # Tom Yum Soup
    
    # American with specific images
    56: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # BBQ Ribs
    57: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Tacos
    58: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop', # Hamburger
    59: 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop', # Mac and Cheese
    60: 'https://images.unsplash.com/photo-1562967916-eb82221dfb92?w=400&h=300&fit=crop', # Fried Chicken
    61: 'https://images.unsplash.com/photo-1621303837174-89787a7d4729?w=400&h=300&fit=crop', # Apple Pie - better pie image
    
    # Middle Eastern with specific images
    62: 'https://images.unsplash.com/photo-1571197119282-7c4fe7c2f9f5?w=400&h=300&fit=crop', # Hummus
    63: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Kebabs
    64: 'https://images.unsplash.com/photo-1601050690117-94f5f6fa44d4?w=400&h=300&fit=crop', # Falafel
    65: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop', # Pizza Margherita
    66: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Shawarma
    67: 'https://images.unsplash.com/photo-1601050690117-94f5f6fa44d4?w=400&h=300&fit=crop', # Pierogies
    68: 'https://images.unsplash.com/photo-1555507036-ab794f77c82d?w=400&h=300&fit=crop', # Butter Croissant
    
    # Korean with authentic Korean food images
    69: 'https://images.unsplash.com/photo-1610415946035-bad6d5b9dbb6?w=400&h=300&fit=crop', # Kimchi
    70: 'https://images.unsplash.com/photo-1548940740-204726a19be3?w=400&h=300&fit=crop', # Bulgogi
    71: 'https://images.unsplash.com/photo-1498654896293-37aacf113fd9?w=400&h=300&fit=crop', # Bibimbap
    72: 'https://images.unsplash.com/photo-1562967916-eb82221dfb92?w=400&h=300&fit=crop', # Korean Fried Chicken
    73: 'https://images.unsplash.com/photo-1553621042-f6e147245754?w=400&h=300&fit=crop', # Japchae
    74: 'https://images.unsplash.com/photo-1601050690117-94f5f6fa44d4?w=400&h=300&fit=crop', # Korean Corn Dog
    75: 'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=300&fit=crop', # Tteokbokki
    76: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Korean Fried Rice
    
    # Brazilian with authentic Brazilian food images
    77: 'https://images.unsplash.com/photo-1583395922949-5ff8fc2f87cf?w=400&h=300&fit=crop', # Feijoada
    78: 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop', # Brigadeiros
    79: 'https://images.unsplash.com/photo-1601050690117-94f5f6fa44d4?w=400&h=300&fit=crop', # Coxinha
    80: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Moqueca
    81: 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop', # Pão de Açúcar
    82: 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400&h=300&fit=crop', # Açaí Bowl
    
    # Vietnamese with specific Vietnamese food images
    83: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Banh Mi
    84: 'https://images.unsplash.com/photo-1559847844-d2104c53b694?w=400&h=300&fit=crop', # Fresh Spring Rolls
    85: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # Bun Bo Hue
    86: 'https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400&h=300&fit=crop', # Vietnamese Coffee
    
    # European with more specific images
    87: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # Bouillabaisse
    88: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # French Onion Soup
    89: 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop', # Crème Brûlée
    90: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Bangers and Mash
    91: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Shepherd's Pie
    92: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Beef Wellington
    93: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Sauerbraten
    94: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Schnitzel
    95: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Beef Stroganoff
    96: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Swedish Meatballs
    97: 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400&h=300&fit=crop', # Dutch Pancakes
    98: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', # Spanish Tortilla
    99: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Goulash
    
    # American Regional with specific images
    100: 'https://images.unsplash.com/photo-1559847844-5315695dadae?w=400&h=300&fit=crop', # New England Clam Chowder
    101: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Jambalaya
    102: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Philly Cheesesteak
    103: 'https://images.unsplash.com/photo-1562967916-eb82221dfb92?w=400&h=300&fit=crop', # Buffalo Wings
    104: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', # Fish Tacos
    
    # Canadian & Australian with specific images
    105: 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', # Poutine
    106: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Tourtière
    107: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Australian Meat Pie
    108: 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop', # Pavlova
    109: 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400&h=300&fit=crop', # Maple Glazed Salmon
    
    # Italian with specific images
    110: 'https://images.unsplash.com/photo-1563379091339-03246963d51a?w=400&h=300&fit=crop', # Risotto
    111: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop', # Osso Buco
}

def update_recipe_images():
    """Update all recipe images with food-specific URLs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🍽️  Updating recipe images with food-specific photos...")
    
    # Update each recipe with its corresponding food image
    for recipe_id, image_url in better_food_images.items():
        try:
            cursor.execute(
                "UPDATE recipes SET image = ? WHERE id = ?",
                (image_url, recipe_id)
            )
            
            # Get recipe name for confirmation
            cursor.execute("SELECT name FROM recipes WHERE id = ?", (recipe_id,))
            recipe_name = cursor.fetchone()
            if recipe_name:
                print(f"✅ Updated {recipe_name[0]} (ID: {recipe_id})")
        except Exception as e:
            print(f"❌ Error updating recipe {recipe_id}: {e}")
    
    # Commit all changes
    conn.commit()
    print(f"\n🎉 Successfully updated {len(better_food_images)} recipes with food-specific images!")
    
    # Verify updates
    cursor.execute("SELECT COUNT(*) FROM recipes WHERE image LIKE '%unsplash%'")
    total_with_images = cursor.fetchone()[0]
    print(f"📊 Total recipes with images: {total_with_images}")
    
    conn.close()

if __name__ == "__main__":
    update_recipe_images()

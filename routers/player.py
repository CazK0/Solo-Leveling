from fastapi import APIRouter
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from database import get_db_connection
import random
from datetime import datetime, timedelta, date

router = APIRouter()

class QuestPayLoad(BaseModel):
    quest_id: str

class BuyPayLoad(BaseModel):
    item_name: str

class DeployPayload(BaseModel):
    raid_type: str

QUEST_DATABASE = {
    "pushups": {"name": "50 Pushups", "xp": 50, "gold": 20},
    "running": {"name": "5km Walk", "xp": 100, "gold": 50},
    "reading": {"name": "Code for 2+ hours", "xp": 30, "gold": 10},
    "water": {"name": "Drink 2L Water", "xp": 10, "gold": 5}
}

SHOP_DATABASE = {
    "potion": {"name": "Health Potion", "cost": 50},
    "game": {"name": "1 Hr Video Games", "cost": 100},
    "cheat_meal": {"name": "Cheat Meal", "cost": 200}
}

RAID_CONFIG = {
    "scout_2h": {"hours": 2, "survival": 95, "name": "C-Rank Scout"},
    "grind_8h": {"hours": 8, "survival": 70, "name": "B-Rank Grind"},
    "boss_24h": {"hours": 24, "survival": 40, "name": "S-Rank Boss Raid"}
}

@router.get("/status")
def get_status():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        player_name VARCHAR(50),
        item_name VARCHAR(100),
        quantity INT DEFAULT 1
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_quests (
        player_name VARCHAR(50),
        quest_id VARCHAR(50),
        last_completed DATE,
        PRIMARY KEY (player_name, quest_id)
        );
        """)
        conn.commit()

        cursor.execute("SELECT * FROM players WHERE name = 'Caz';")
        player_data = cursor.fetchone()

        cursor.execute("SELECT item_name, quantity FROM inventory WHERE player_name = 'Caz';")
        inventory_data = cursor.fetchall()

        today = date.today()
        cursor.execute("SELECT quest_id FROM daily_quests WHERE player_name = 'Caz' AND last_completed = %s;", (today,))
        completed_data = [row['quest_id'] for row in cursor.fetchall()]

        return {
            "System_Status": "Online",
            "Player": player_data,
            "Inventory": inventory_data,
            "Completed_Today": completed_data
        }
    finally:
        cursor.close()
        conn.close()

@router.post("/quest/complete")
def complete_quest(payload: QuestPayLoad):
    clicked_quest = payload.quest_id
    if clicked_quest not in QUEST_DATABASE:
        return {"System_Alert": "Quest not found", "Success": False}

    reward = QUEST_DATABASE[clicked_quest]
    today = date.today()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT last_completed FROM daily_quests WHERE player_name = 'Caz' AND quest_id = %s;",
                       (clicked_quest,))
        record = cursor.fetchone()

        if record and record['last_completed'] == today:
            return {"System_Alert": "Quest already completed today!", "Success": False}

        cursor.execute("""
        UPDATE players 
        SET xp = xp + %s, gold = gold + %s
        WHERE name = 'Caz'
        RETURNING *;
        """, (reward['xp'], reward['gold']))
        player = cursor.fetchone()

        if player['xp'] >= player['xp_to_next_level']:
            overflow_xp = player['xp'] - player['xp_to_next_level']
            new_threshold = int(player['xp_to_next_level'] * 1.5)

            cursor.execute("""
            UPDATE players
            SET level = level + 1, xp = %s, xp_to_next_level = %s, stat_points = stat_points + 5
            WHERE name = 'Caz'
            RETURNING *;
            """, (overflow_xp, new_threshold))
            player = cursor.fetchone()
            system_message = f"LEVEL UP! You are now level {player['level']}! +5 Stat Points Awarded!"
        else:
            system_message = f"Quest Complete: {reward['name']}. +{reward['xp']} XP."

        cursor.execute("""
        INSERT INTO daily_quests (player_name, quest_id, last_completed)
        VALUES ('Caz', %s, %s)
        ON CONFLICT (player_name, quest_id) 
        DO UPDATE SET last_completed = EXCLUDED.last_completed;
        """, (clicked_quest, today))

        conn.commit()
        return {"System_Alert": system_message, "New_Status": player, "Success": True}
    finally:
        cursor.close()
        conn.close()

@router.post("/shop/buy")
def buy_item(payload: BuyPayLoad):
    item_key = payload.item_name
    if item_key not in SHOP_DATABASE:
        return {"System_Alert": "Item not in shop", "Success": False}
    item = SHOP_DATABASE[item_key]
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT gold FROM players WHERE name = 'Caz';")
        player = cursor.fetchone()
        if player['gold'] < item['cost']:
            return {"System_Alert": "Not enough gold!", "Success": False}

        cursor.execute("""
        UPDATE players
        SET gold = gold - %s
        WHERE name = 'Caz';
        """, (item['cost'],))

        cursor.execute("""
        SELECT * FROM inventory WHERE player_name = 'Caz' AND item_name = %s;
        """, (item['name'],))
        existing_item = cursor.fetchone()

        if existing_item:
            cursor.execute("""
            UPDATE inventory SET quantity = quantity + 1
            WHERE player_name = 'Caz' AND item_name = %s;
            """, (item['name'],))
        else:
            cursor.execute("""
            INSERT INTO inventory (player_name, item_name, quantity)
            VALUES ('Caz', %s, 1);
            """, (item['name'],))
        conn.commit()
        return {"System_Alert": f"Purchased: {item['name']}!", "Success": True}
    finally:
        cursor.close()
        conn.close()

@router.post("/system/allocate-stat")
def allocate_stat(stat: str):
    valid_stats = ["strength", "agility", "intelligence", "perception"]
    if stat not in valid_stats:
        return {"System_Alert": "Invalid stat selected.", "Success": False}

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT stat_points FROM players WHERE name = 'Caz';")
        player = cursor.fetchone()

        if player['stat_points'] <= 0:
            return {"System_Alert": "Not enough Stat Points!", "Success": False}

        query = f"""
            UPDATE players 
            SET {stat} = {stat} + 1, stat_points = stat_points - 1
            WHERE name = 'Caz'
            RETURNING *;
        """
        cursor.execute(query)
        conn.commit()
        return {"System_Alert": f"Stat Allocated: +1 {stat.capitalize()}!", "Success": True}
    finally:
        cursor.close()
        conn.close()

@router.post("/system/reset")
def reset_system():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
        UPDATE players 
        SET level = 1, xp = 0, xp_to_next_level = 100, gold = 0, 
            strength = 10, agility = 10, intelligence = 10, perception = 10, stat_points = 0
        WHERE name = 'Caz';
        """)
        cursor.execute("DELETE FROM inventory WHERE player_name = 'Caz';")
        cursor.execute("DELETE FROM daily_quests WHERE player_name = 'Caz';")
        conn.commit()
        return {"System_Alert": "SYSTEM HARD RESET COMPLETE.", "Success": True}
    finally:
        cursor.close()
        conn.close()

@router.post("/shadow/deploy")
def deploy_shadow(payload: DeployPayload):
    raid_key = payload.raid_type
    if raid_key not in RAID_CONFIG:
        return {"System_Alert": "Invalid gate selected.", "Success": False}

    raid = RAID_CONFIG[raid_key]
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM shadow_expeditions WHERE player_name = 'Caz' AND status = 'mining';")
        active_raid = cursor.fetchone()
        if active_raid:
            return {"System_Alert": "A shadow is already deployed!", "Success": False}

        now = datetime.now()
        return_time = now + timedelta(hours=raid['hours'])

        cursor.execute("""
                       INSERT INTO shadow_expeditions (player_name, raid_type, start_time, return_time, status)
                       VALUES ('Caz', %s, %s, %s, 'mining');
                       """, (raid_key, now, return_time))

        conn.commit()
        return {"System_Alert": f"Shadow deployed to {raid['name']}. Returning in {raid['hours']} hours.",
                "Success": True}
    finally:
        cursor.close()
        conn.close()

@router.post("/shadow/claim")
def claim_shadow():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM shadow_expeditions WHERE player_name = 'Caz' AND status = 'mining';")
        raid = cursor.fetchone()

        if not raid:
            return {"System_Alert": "No shadow currently deployed.", "Success": False}

        now = datetime.now()
        if now < raid['return_time']:
            time_left = raid['return_time'] - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return {"System_Alert": f"Shadow still mining. Time remaining: {hours}h {minutes}m.", "Success": False}
        config = RAID_CONFIG[raid['raid_type']]
        roll = random.randint(1, 100)

        cursor.execute("UPDATE shadow_expeditions SET status = 'completed' WHERE id = %s;", (raid['id'],))

        if roll > config['survival']:
            conn.commit()
            return {"System_Alert": f"SYSTEM WARNING: Shadow was destroyed in the {config['name']}.", "Success": True,
                    "Survived": False}
        system_message = ""
        if raid['raid_type'] == "scout_2h":
            gold_found = random.randint(30, 80)
            cursor.execute("UPDATE players SET gold = gold + %s WHERE name = 'Caz';", (gold_found,))

            cursor.execute("SELECT * FROM inventory WHERE player_name = 'Caz' AND item_name = 'Health Potion';")
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE inventory SET quantity = quantity + 1 WHERE player_name = 'Caz' AND item_name = 'Health Potion';")
            else:
                cursor.execute(
                    "INSERT INTO inventory (player_name, item_name, quantity) VALUES ('Caz', 'Health Potion', 1);")

            system_message = f"Scout Successful! Found {gold_found} Gold and 1 Health Potion."

        elif raid['raid_type'] == "grind_8h":
            xp_found = random.randint(150, 300)
            cursor.execute("UPDATE players SET xp = xp + %s WHERE name = 'Caz' RETURNING *;", (xp_found,))

            system_message = f"Grind Successful! Shadow extracted {xp_found} XP."

        elif raid['raid_type'] == "boss_24h":
            cursor.execute("UPDATE players SET stat_points = stat_points + 1 WHERE name = 'Caz';")
            system_message = "BOSS DEFEATED! Extracted 1 pure Stat Point!"

        conn.commit()
        return {"System_Alert": system_message, "Success": True, "Survived": True}
    finally:
        cursor.close()
        conn.close()

@router.get("/{name}")
def get_player(name: str):
    return {
        "name": "Caz",
        "level": 999,
        "job_class": "System Architect",
        "strength": 500,
        "agility": 500
    }
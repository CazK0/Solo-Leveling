import { useState, useEffect } from 'react'
import './index.css'

const API_URL = "https://solo-leveling-8obi.onrender.com"

function App() {
  const [player, setPlayer] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [completedQuests, setCompletedQuests] = useState([]);
  const [alertMsg, setAlertMsg] = useState("");
  const [selectedQuest, setSelectedQuest] = useState("pushups");
  const [showLevelUp, setShowLevelUp] = useState(false);
  const [selectedRaid, setSelectedRaid] = useState("scout_2h");

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/status`);
      const data = await response.json();
      setPlayer(data.Player);
      setInventory(data.Inventory);
      setCompletedQuests(data.Completed_Today || []);
    } catch (error) {
      setAlertMsg("SYSTEM ERROR: Cannot connect to server.");
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const completeQuest = async () => {
    try {
      const response = await fetch(`${API_URL}/quest/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quest_id: selectedQuest })
      });
      const data = await response.json();

      setAlertMsg(data.System_Alert);

      if (data.System_Alert && data.System_Alert.includes("LEVEL UP")) {
          setShowLevelUp(true);
      }

      if (data.Success) fetchStats();
    } catch (error) {
      setAlertMsg("Quest Failed to Send.");
    }
  };

  const deployShadow = async () => {
    try {
      const response = await fetch(`${API_URL}/shadow/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raid_type: selectedRaid })
      });
      const data = await response.json();
      setAlertMsg(data.System_Alert);
    } catch (error) {
      setAlertMsg("System Error: Failed to deploy shadow.");
    }
  };

  const claimShadow = async () => {
    try {
      const response = await fetch(`${API_URL}/shadow/claim`, {
        method: 'POST'
      });
      const data = await response.json();
      setAlertMsg(data.System_Alert);

      if (data.Success && data.Survived) {
          fetchStats();
      }
    } catch (error) {
      setAlertMsg("System Error: Failed to extract shadow.");
    }
  };

  const allocateStat = async (statName) => {
    try {
      const response = await fetch(`${API_URL}/system/allocate-stat?stat=${statName}`, { method: 'POST' });
      const data = await response.json();
      setAlertMsg(data.System_Alert);
      if (data.Success) fetchStats();
    } catch (error) {
      setAlertMsg("System Error: Allocation Failed.");
    }
  };

  const buyItem = async (itemKey) => {
    try {
      const response = await fetch(`${API_URL}/shop/buy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_name: itemKey })
      });
      const data = await response.json();
      setAlertMsg(data.System_Alert);
      if (data.Success) fetchStats();
    } catch (error) {
      setAlertMsg("Transaction Failed.");
    }
  };

  const resetSystem = async () => {
    try {
        const response = await fetch(`${API_URL}/system/reset`, { method: 'POST' });
        const data = await response.json();
        setAlertMsg(data.System_Alert);
        if (data.Success) fetchStats();
    } catch (error) {
        setAlertMsg("System Reset Failed.");
    }
  };

  if (!player) {
    return <div className="status-window"><h1>CONNECTING TO SYSTEM...</h1></div>;
  }

  const xpPercentage = Math.min((player.xp / player.xp_to_next_level) * 100, 100);
  const isSelectedCompleted = completedQuests.includes(selectedQuest);

  return (
    <>
      {showLevelUp && (
        <div className="overlay" onClick={() => setShowLevelUp(false)}>
          <div className="level-up-card">
            <h2>LEVEL UP</h2>
            <p>You have reached Level {player.level}!</p>
            <p style={{color: '#00ffcc'}}>+5 Stat Points Awarded</p>
            <button className="btn" onClick={() => setShowLevelUp(false)}>CONTINUE</button>
          </div>
        </div>
      )}

      <div className="status-window" style={{ width: '420px', position: 'relative' }}>
        <h1>STATUS</h1>
        <div className="stat-line"><span>NAME:</span> <span>{player.name}</span></div>
        <div className="stat-line"><span>LEVEL:</span> <span className="highlight">{player.level}</span></div>
        <div className="stat-line"><span>GOLD:</span> <span>{player.gold}</span></div>

        <div className="stat-line" style={{flexDirection: 'column', alignItems: 'flex-start', borderBottom: 'none'}}>
            <span>XP:</span>
            <div className="xp-bar-container">
                <div className="xp-bar-fill" style={{ width: `${xpPercentage}%` }}></div>
                <div className="xp-text-overlay">{player.xp} / {player.xp_to_next_level}</div>
            </div>
        </div>

        <br />

        <div className="stat-line"><span>STR:</span> <span><span>{player.strength}</span> <button className="plus-btn" onClick={() => allocateStat('strength')}>[+]</button></span></div>
        <div className="stat-line"><span>AGI:</span> <span><span>{player.agility}</span> <button className="plus-btn" onClick={() => allocateStat('agility')}>[+]</button></span></div>
        <div className="stat-line"><span>INT:</span> <span><span>{player.intelligence}</span> <button className="plus-btn" onClick={() => allocateStat('intelligence')}>[+]</button></span></div>
        <div className="stat-line"><span>PER:</span> <span><span>{player.perception}</span> <button className="plus-btn" onClick={() => allocateStat('perception')}>[+]</button></span></div>
        <div className="stat-line highlight"><span>STAT POINTS:</span> <span>{player.stat_points}</span></div>

        <br />

        <h2 style={{ textAlign: 'center', margin: '10px 0', fontSize: '18px', color: '#ffcc00', letterSpacing: '1px' }}>SYSTEM SHOP</h2>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
          <button className="btn" style={{ marginTop: 0, padding: '10px 5px', fontSize: '13px' }} onClick={() => buyItem('potion')}>Potion (50G)</button>
          <button className="btn" style={{ marginTop: 0, padding: '10px 5px', fontSize: '13px' }} onClick={() => buyItem('game')}>Game Hr (100G)</button>
          <button className="btn" style={{ marginTop: 0, padding: '10px 5px', fontSize: '13px' }} onClick={() => buyItem('cheat_meal')}>Meal (200G)</button>
        </div>

        <br />

        <h2 style={{ textAlign: 'center', margin: '10px 0', fontSize: '18px', color: '#00ffcc', letterSpacing: '1px' }}>INVENTORY</h2>
        <div style={{ minHeight: '60px', backgroundColor: 'rgba(0, 20, 40, 0.9)', border: '1px solid #00ffcc', padding: '10px', borderRadius: '5px' }}>
          {inventory.length === 0 ? <p style={{ textAlign: 'center', margin: 0, color: '#4da6ff', fontStyle: 'italic' }}>Inventory Empty</p> :
            inventory.map((item, index) => (
              <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', borderBottom: '1px solid rgba(0, 255, 204, 0.3)' }}>
                <span>{item.item_name}</span>
                <span style={{ color: '#00ffcc', fontWeight: 'bold' }}>x{item.quantity}</span>
              </div>
            ))
          }
        </div>

        <div style={{ marginTop: '25px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <select
                value={selectedQuest}
                onChange={(e) => setSelectedQuest(e.target.value)}
                style={{ padding: '10px', backgroundColor: '#001428', color: '#4da6ff', border: '1px solid #4da6ff', borderRadius: '5px', fontSize: '14px' }}
            >
                <option value="pushups">{completedQuests.includes("pushups") ? "[DONE] 50 Pushups" : "50 Pushups (50 XP | 20 Gold)"}</option>
                <option value="running">{completedQuests.includes("running") ? "[DONE] 5km Walk" : "5km Walk (100 XP | 50 Gold)"}</option>
                <option value="reading">{completedQuests.includes("reading") ? "[DONE] Code for 2+ hours" : "Code for 2+ hours (30 XP | 10 Gold)"}</option>
                <option value="water">{completedQuests.includes("water") ? "[DONE] Drink 2L Water" : "Drink 2L Water (10 XP | 5 Gold)"}</option>
            </select>
            <button
                className="btn"
                onClick={completeQuest}
                disabled={isSelectedCompleted}
                style={{
                    backgroundColor: isSelectedCompleted ? '#333' : '#4da6ff',
                    color: isSelectedCompleted ? '#666' : '#000',
                    cursor: isSelectedCompleted ? 'not-allowed' : 'pointer',
                    boxShadow: isSelectedCompleted ? 'none' : ''
                }}
            >
                {isSelectedCompleted ? "QUEST COMPLETED TODAY" : "COMPLETE SELECTED QUEST"}
            </button>
        </div>

        <div id="alert-box">{alertMsg}</div>

        <br />
        <h2 style={{ textAlign: 'center', margin: '10px 0', fontSize: '18px', color: '#9933ff', letterSpacing: '1px', textShadow: '0 0 5px #9933ff' }}>
          SHADOW ARMY
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
            <select
                value={selectedRaid}
                onChange={(e) => setSelectedRaid(e.target.value)}
                style={{ padding: '10px', backgroundColor: '#1a0033', color: '#cc99ff', border: '1px solid #9933ff', borderRadius: '5px', fontSize: '14px', outline: 'none' }}
            >
                <option value="scout_2h">C-Rank Scout (2 Hours | 95% Survival | Gold/Potions)</option>
                <option value="grind_8h">B-Rank Grind (8 Hours | 70% Survival | Raw XP)</option>
                <option value="boss_24h">S-Rank Boss (24 Hours | 40% Survival | Stat Point)</option>
            </select>

            <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className="btn"
                  onClick={deployShadow}
                  style={{ backgroundColor: '#9933ff', color: '#fff', flex: 1, boxShadow: '0 0 10px rgba(153, 51, 255, 0.4)' }}
                >
                  ARISE (DEPLOY)
                </button>
                <button
                  className="btn"
                  onClick={claimShadow}
                  style={{ backgroundColor: '#1a0033', color: '#cc99ff', border: '1px solid #9933ff', flex: 1 }}
                >
                  EXTRACT LIVES
                </button>
            </div>
        </div>
        <button
            onClick={resetSystem}
            style={{marginTop: '40px', backgroundColor: '#8b0000', color: '#fff', padding: '10px', border: 'none', borderRadius: '5px', cursor: 'pointer', width: '100%', fontWeight: 'bold', letterSpacing: '1px'}}
        >
            [DEV] HARD RESET SYSTEM
        </button>
      </div>
    </>
  )
}

export default App
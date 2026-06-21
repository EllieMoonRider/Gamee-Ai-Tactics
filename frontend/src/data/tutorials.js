// Tutorial / walkthrough content for the Command Center dropdown
export const TUTORIALS = [
  {
    id: "deep-dive",
    label: "CypherAI Deep Dive — Account Baselining",
    duration: "2 min",
    steps: [
      { title: "Pick a title & open Deep Dive tab", body: "Inside a game's workspace, open the Deep Dive tab. This is where CypherAI reads your account." },
      { title: "Upload screenshots", body: "Drop up to 6 screenshots of your heroes, HQ, formation, gear, alliance, resources — anything CypherAI should see." },
      { title: "Add context (optional)", body: "Tell CypherAI your play style — F2P, focusing on cavalry, prepping for KvK. The deeper the context, the sharper the analysis." },
      { title: "Read the baseline", body: "Account Snapshot, Strengths, Weaknesses, Top 5 Actions, Resource Split, 30/60/90 Milestones." },
      { title: "Stack Building Blocks", body: "Every time you make progress, upload fresh screenshots as a Follow-Up. CypherAI compares to baseline and updates priorities — your tactical archive grows." },
    ],
  },
  {
    id: "getting-started",
    label: "Mission Briefing — First Time Here",
    duration: "2 min",
    steps: [
      { title: "Pick your title", body: "Open the Command Center, scroll to your game grid, and click the title you're playing. Each title has its own dedicated tactical workspace." },
      { title: "Open the AI Tactical Ally", body: "Inside your game workspace, open the AI Chat tab. Ask anything — meta heroes, event prep, F2P paths. Responses stream live." },
      { title: "Track your progress", body: "Use the Daily Planner tab to log objectives. They're color-coded by priority (low/med/high)." },
      { title: "Save your strategy", body: "Use the Build Optimizer for AI-generated team comps, and bookmark Guides relevant to your title." },
    ],
  },
  {
    id: "ai-chat",
    label: "AI Tactical Ally — Chat Walkthrough",
    duration: "1 min",
    steps: [
      { title: "Start a new chat", body: "Click 'New chat' inside any game's Chat tab. Each session is scoped to that specific title." },
      { title: "Ask in plain language", body: "No prompt-engineering required. Examples: 'What's the best F2P hero for arena?' or 'Rush priority for HQ20'." },
      { title: "Multi-turn aware", body: "Your Ally remembers the last ~10 messages in a session. Use follow-ups instead of repeating context." },
      { title: "Manage history", body: "Switch between past chats via the sidebar. Delete any chat with the trash icon on hover." },
    ],
  },
  {
    id: "optimizer",
    label: "Build Optimizer — Tactical Outputs",
    duration: "1 min",
    steps: [
      { title: "Define an objective", body: "Be specific: 'Win Kingdom War Saturday' beats 'Get stronger'." },
      { title: "List your roster", body: "Drop hero names + levels. The Ally weighs synergies and tier." },
      { title: "Add resources", body: "Mention gems, speedups, shards. Output adapts allocation %." },
      { title: "Read the 4-block plan", body: "RECOMMENDED TEAM → PRIORITY UPGRADES → RESOURCE ALLOCATION → WARNINGS." },
    ],
  },
  {
    id: "planner",
    label: "Daily Planner — Stay on Mission",
    duration: "1 min",
    steps: [
      { title: "Add a task per game", body: "Tasks are filed under the active game tab. Use them for dailies, alliance duties, event timers." },
      { title: "Prioritize", body: "Mark high (red), med (amber), low (green). Sort by what matters today." },
      { title: "Tick or wipe", body: "Toggle the checkbox when done. Open Tasks count is visible on the Command Center stat panel." },
    ],
  },
  {
    id: "guides",
    label: "Guide Library — Use Curated Knowledge",
    duration: "1 min",
    steps: [
      { title: "Filter by title", body: "Each game has its own curated guides covering beginner roadmaps, hero tier lists, event tactics." },
      { title: "Read the brief", body: "Each guide shows category + summary. Click to expand the full tactical block." },
      { title: "Combine with the Ally", body: "Paste a guide point into AI Chat to get a personalized version for your situation." },
    ],
  },
];

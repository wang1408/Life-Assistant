import { useEffect, useRef, useState } from "react";
import { completeTodo, confirmAction, createConversation, createTodo, deleteConversation, deleteTodo, getConversationMessages, getConversations, getDashboard, sendChat, updateTodo, type Conversation } from "./api/client";

type Message = { role: "user" | "assistant"; content: string; results?: { travel?: any; weather?: any; advice?: any } };
type Dashboard = { todos: any[]; memories: any[]; pending_actions: any[] };

function formatDistance(value: any) {
  const meters = Number(value);
  if (!Number.isFinite(meters)) return "—";
  return meters >= 1000 ? `${(meters / 1000).toFixed(1)} km` : `${Math.round(meters)} m`;
}

function formatDuration(value: any) {
  const seconds = Number(value);
  if (!Number.isFinite(seconds)) return "—";
  const minutes = Math.max(1, Math.round(seconds / 60));
  return minutes >= 60 ? `${Math.floor(minutes / 60)}小时${minutes % 60 ? ` ${minutes % 60}分` : ""}` : `${minutes}分钟`;
}

function TripWidget({ results }: { results: { travel?: any; weather?: any; advice?: any } }) {
  const route = results.travel;
  const weather = results.weather;
  const advice = results.advice;
  const now = weather?.now;
  const hasRoute = Boolean(route);
  const hasWeather = Boolean(weather);
  const hasAdvice = Boolean(advice?.text);
  const showWeather = hasWeather && !hasAdvice;
  const title = hasAdvice ? "出行建议" : hasRoute && hasWeather ? "出行方案" : hasRoute ? "路线规划" : "天气状况";
  const badge = hasAdvice ? "天气驱动" : hasRoute && hasWeather ? "路线 + 天气" : hasRoute ? "路线" : "天气";
  return <div className="trip-widget">
    <div className="trip-title"><div><span className="eyebrow">SMART TRIP</span><h3>{title}</h3></div><span className="trip-badge">{badge}</span></div>
    <div className={`trip-columns ${[hasRoute, showWeather, hasAdvice].filter(Boolean).length > 1 ? "" : "single"}`}>
      {hasAdvice && <div className="advice-pane">
        <div className="pane-title"><span className="pane-icon advice-icon">✓</span><div><strong>智能出行建议</strong><small>根据{weather?.location || "当前位置"}实时天气</small></div></div>
        <div className="advice-text">{advice.text}</div>
        {now && <div className="advice-reference">参考天气：{now.temp ?? "—"}℃，{now.text || "实时天气"}，降水 {now.precip ?? "—"} mm，风力 {now.windScale ?? "—"} 级</div>}
      </div>}
      {hasRoute && <div className="route-pane">
        <div className="pane-title"><span className="pane-icon route-icon">↗</span><div><strong>高德路线</strong><small>{route?.available ? "已规划驾车路线" : "路线暂不可用"}</small></div></div>
        {route?.map_url ? <img className="route-map" src={route.map_url} alt="高德路线地图" /> : <div className="route-map map-empty"><span>⌖</span><p>{route?.message || "输入城市或具体地址即可生成地图"}</p></div>}
        <div className="route-points"><span className="point start" /> <span>{route?.origin || "出发地"}</span><span className="route-line" /><span className="point end" /> <span>{route?.destination || "目的地"}</span></div>
        <div className="route-footer"><div><small>距离</small><strong>{formatDistance(route?.distance)}</strong></div><div><small>预计用时</small><strong>{formatDuration(route?.duration)}</strong></div>{route?.navigation_url && <a href={route.navigation_url} target="_blank" rel="noreferrer">打开高德导航 ↗</a>}</div>
      </div>}
      {showWeather && <div className="weather-pane">
        <div className="pane-title"><span className="pane-icon weather-icon">☼</span><div><strong>{hasRoute ? "目的地天气" : "当前天气"}</strong><small>{weather?.location || (hasRoute ? "出行地点" : "当前位置")}</small></div></div>
        {weather?.available && now ? <><div className="weather-main"><span className="weather-temp">{now.temp}°</span><div><strong>{now.text || "实时天气"}</strong><span>体感 {now.feelsLike || "—"}°</span></div></div><div className="weather-details"><span>💧 湿度 {now.humidity || "—"}%</span><span>↟ {now.windDir || "风力"} {now.windScale || "—"}级</span></div><div className="weather-tip">{Number(now.precip || 0) > 0 ? "有降水，建议携带雨具" : "当前无明显降水，适合出行"}</div></> : <div className="weather-empty"><span>☁</span><p>{weather?.message || "请输入城市或具体地点查询天气"}</p></div>}
      </div>}
    </div>
  </div>;
}

function getBrowserLocation(): Promise<string | undefined> {
  if (!navigator.geolocation) return Promise.resolve(undefined);
  return new Promise(resolve => navigator.geolocation.getCurrentPosition(
    position => resolve(`${position.coords.longitude},${position.coords.latitude}`),
    () => resolve(undefined),
    { enableHighAccuracy: false, timeout: 5000, maximumAge: 300000 },
  ));
}

function toDateTimeLocal(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value);
  const pad = (number: number) => String(number).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard>({ todos: [], memories: [], pending_actions: [] });
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [conversationLoading, setConversationLoading] = useState(true);
  const [location, setLocation] = useState<string | undefined>();
  const [locationStatus, setLocationStatus] = useState("未定位");
  const [todoTitle, setTodoTitle] = useState("");
  const [todoRemindAt, setTodoRemindAt] = useState("");
  const [editingTodoId, setEditingTodoId] = useState<number | null>(null);
  const [editingTodoTitle, setEditingTodoTitle] = useState("");
  const [editingTodoRemindAt, setEditingTodoRemindAt] = useState("");
  const refresh = () => { void getDashboard().then(setDashboard).catch(() => undefined); };
  const initialized = useRef(false);
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    void (async () => {
      try {
        let items = await getConversations();
        if (!items.length) {
          const created = await createConversation();
          items = [created];
        }
        setConversations(items);
        await selectConversation(items[0].id);
      } finally {
        setConversationLoading(false);
      }
    })();
    refresh();
  }, []);
  useEffect(() => {
    const timer = window.setInterval(refresh, 15000);
    return () => window.clearInterval(timer);
  }, []);
  async function selectConversation(id: number) {
    setConversationLoading(true);
    try {
      const stored = await getConversationMessages(id);
      setActiveConversationId(id);
    setMessages(stored.map(message => ({ role: message.role, content: message.content, results: message.result_json?.travel || message.result_json?.weather || message.result_json?.advice ? message.result_json : undefined })));
    } finally {
      setConversationLoading(false);
    }
  }
  async function createSession() {
    const created = await createConversation();
    setConversations(items => [created, ...items]);
    setActiveConversationId(created.id);
    setMessages([]);
    setInput("");
  }
  async function removeSession(id: number) {
    if (!window.confirm("确定删除这个会话及其全部消息吗？")) return;
    await deleteConversation(id);
    const remaining = conversations.filter(item => item.id !== id);
    if (!remaining.length) {
      const created = await createConversation();
      setConversations([created]);
      setActiveConversationId(created.id);
      setMessages([]);
      return;
    }
    setConversations(remaining);
    if (id === activeConversationId) await selectConversation(remaining[0].id);
  }
  async function locate() {
    setLocationStatus("定位中…");
    const value = await getBrowserLocation();
    if (value) {
      setLocation(value);
      setLocationStatus("已定位");
    } else {
      setLocationStatus("定位未授权");
    }
  }
  async function addTodo() {
    if (!todoTitle.trim()) return;
    await createTodo({ title: todoTitle.trim(), remind_at: todoRemindAt ? new Date(todoRemindAt).toISOString() : null, due_at: todoRemindAt ? new Date(todoRemindAt).toISOString() : null });
    setTodoTitle("");
    setTodoRemindAt("");
    refresh();
  }
  function beginTodoEdit(todo: any) {
    setEditingTodoId(todo.id);
    setEditingTodoTitle(todo.title);
    setEditingTodoRemindAt(toDateTimeLocal(todo.remind_at));
  }
  async function saveTodoEdit() {
    if (!editingTodoId || !editingTodoTitle.trim()) return;
    await updateTodo(editingTodoId, { title: editingTodoTitle.trim(), remind_at: editingTodoRemindAt ? new Date(editingTodoRemindAt).toISOString() : null, due_at: editingTodoRemindAt ? new Date(editingTodoRemindAt).toISOString() : null });
    setEditingTodoId(null);
    refresh();
  }
  async function finishTodo(id: number) {
    await completeTodo(id);
    refresh();
  }
  async function removeTodo(id: number) {
    if (!window.confirm("确定删除这个待办吗？")) return;
    await deleteTodo(id);
    refresh();
  }
  async function submit() {
    if (!input.trim() || loading) return;
    const text = input.trim(); setInput(""); setMessages(m => [...m, { role: "user", content: text }]); setLoading(true);
    try { const currentLocation = /我所在地|当前位置|当前地点|当前地|本地|附近/.test(text) ? (location || await getBrowserLocation()) : location; await sendChat(text, event => { if (event.type === "message") setMessages(m => [...m, { role: "assistant", content: event.content }]); if (event.type === "results" && (event.data?.travel || event.data?.weather || event.data?.advice)) setMessages(m => { const next = [...m]; const index = [...next].reverse().findIndex(item => item.role === "assistant"); if (index >= 0) next[next.length - 1 - index] = { ...next[next.length - 1 - index], results: event.data }; return next; }); }, currentLocation, activeConversationId || undefined); setConversations(await getConversations()); refresh(); }
    catch (e) { setMessages(m => [...m, { role: "assistant", content: "服务暂时不可用，请检查后端。" }]); }
    finally { setLoading(false); }
  }
  return <main className="shell">
    <header><div><h1>Life Assistant</h1><p>你的多 Agent 生活助手</p></div><div className="header-actions"><button className="new-session" onClick={() => void createSession()}>＋ 新建会话</button><span className="status">● 本机服务</span></div></header>
    <section className="workspace"><aside className="sidebar"><div className="sidebar-head"><h2>会话</h2><button className="sidebar-plus" onClick={() => void createSession()}>＋</button></div><button className="sidebar-new" onClick={() => void createSession()}>＋ 新建会话</button><div className="session-list">{conversations.map(item => <div className={`session-item ${item.id === activeConversationId ? "selected" : ""}`} key={item.id} onClick={() => void selectConversation(item.id)}><div className="session-info"><strong>{item.title}</strong><small>{new Date(item.created_at).toLocaleDateString()}</small></div><button className="session-delete" aria-label="删除会话" onClick={event => { event.stopPropagation(); void removeSession(item.id); }}>×</button></div>)}</div>{conversationLoading && !conversations.length && <div className="sidebar-loading">正在加载会话…</div>}</aside><div className="grid">
      <div className="panel chat"><h2>对话</h2><div className="messages">{messages.length === 0 && <div className="hint">试试：明天 8:00 提醒我带伞，或者查询从公司到机场的路线和天气。</div>}{messages.map((m, i) => <div key={i}><div className={`bubble ${m.role}`}>{m.content}</div>{m.results && <TripWidget results={m.results} />}</div>)}</div><div className="location-strip"><span className={`location-dot ${location ? "active" : ""}`} />{location ? "已启用当前位置" : "路线查询可使用当前位置"}<button onClick={locate} disabled={locationStatus === "定位中…"}>⌖ {locationStatus}</button></div><div className="composer"><input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && submit()} placeholder="告诉我你想安排什么…"/><button onClick={submit} disabled={loading || !activeConversationId}>发送</button></div></div>
      <div className="panel todo-panel"><div className="panel-title-row"><h2>今日待办</h2><span className="todo-count">{dashboard.todos.length}</span></div><div className="todo-create"><input value={todoTitle} onChange={event => setTodoTitle(event.target.value)} onKeyDown={event => event.key === "Enter" && void addTodo()} placeholder="新增一个待办…"/><input type="datetime-local" value={todoRemindAt} onChange={event => setTodoRemindAt(event.target.value)} title="提醒时间"/><button onClick={() => void addTodo()} disabled={!todoTitle.trim()}>添加</button></div>{dashboard.todos.length ? dashboard.todos.map(t => editingTodoId === t.id ? <div className="todo-edit" key={t.id}><input value={editingTodoTitle} onChange={event => setEditingTodoTitle(event.target.value)}/><input type="datetime-local" value={editingTodoRemindAt} onChange={event => setEditingTodoRemindAt(event.target.value)}/><button onClick={() => void saveTodoEdit()}>保存</button><button className="ghost-button" onClick={() => setEditingTodoId(null)}>取消</button></div> : <div className="todo-row" key={t.id}><button className="todo-check" title="完成待办" onClick={() => void finishTodo(t.id)}>✓</button><div className="todo-content"><strong>{t.title}</strong><small>{t.remind_at ? `提醒：${new Date(t.remind_at).toLocaleString()}` : "未设提醒"}</small></div><button className="todo-action" onClick={() => beginTodoEdit(t)}>编辑</button><button className="todo-action danger" onClick={() => void removeTodo(t.id)}>删除</button></div>) : <div className="empty">暂无待办</div>}</div>
      <div className="panel"><h2>待确认动作</h2>{dashboard.pending_actions.length ? dashboard.pending_actions.map(a => <div className="action" key={a.id}><span>{a.payload?.title || a.action_type}</span><button onClick={() => confirmAction(a.id).then(refresh)}>确认</button></div>) : <div className="empty">没有需要确认的动作</div>}</div>
      <div className="panel"><h2>我的习惯</h2>{dashboard.memories.length ? dashboard.memories.map(m => <div className="row" key={m.id}><span>{m.content}</span><small>{m.enabled ? "已启用" : "已停用"}</small></div>) : <div className="empty">对话后会在这里显示可管理的偏好</div>}</div>
    </div></section>
  </main>;
}

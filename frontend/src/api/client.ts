const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type Conversation = { id: number; title: string; created_at: string };
export type StoredMessage = { id: number; conversation_id: number; role: "user" | "assistant"; content: string; result_json?: { travel?: any; weather?: any; advice?: any }; created_at: string };

export async function getConversations(): Promise<Conversation[]> {
  const response = await fetch(`${API}/api/v1/conversations`);
  if (!response.ok) throw new Error("无法加载会话");
  return response.json();
}

export async function createConversation(): Promise<Conversation> {
  const response = await fetch(`${API}/api/v1/conversations`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
  if (!response.ok) throw new Error("无法创建会话");
  return response.json();
}

export async function getConversationMessages(id: number): Promise<StoredMessage[]> {
  const response = await fetch(`${API}/api/v1/conversations/${id}/messages`);
  if (!response.ok) throw new Error("无法加载会话消息");
  return response.json();
}

export async function deleteConversation(id: number) {
  const response = await fetch(`${API}/api/v1/conversations/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error("无法删除会话");
}

export async function createTodo(payload: { title: string; remind_at?: string | null; due_at?: string | null }) {
  const response = await fetch(`${API}/api/v1/todos`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, priority: 2 }) });
  if (!response.ok) throw new Error("无法创建待办");
  return response.json();
}

export async function updateTodo(id: number, payload: { title?: string; remind_at?: string | null; due_at?: string | null }) {
  const response = await fetch(`${API}/api/v1/todos/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  if (!response.ok) throw new Error("无法更新待办");
  return response.json();
}

export async function completeTodo(id: number) {
  const response = await fetch(`${API}/api/v1/todos/${id}/complete`, { method: "POST" });
  if (!response.ok) throw new Error("无法完成待办");
  return response.json();
}

export async function deleteTodo(id: number) {
  const response = await fetch(`${API}/api/v1/todos/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error("无法删除待办");
}

export async function getDashboard() {
  const response = await fetch(`${API}/api/v1/dashboard/today`);
  if (!response.ok) throw new Error("无法加载仪表盘");
  return response.json();
}

export async function sendChat(message: string, onEvent: (event: any) => void, currentLocation?: string, conversationId?: number) {
  const response = await fetch(`${API}/api/v1/chat/stream`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, current_location: currentLocation, conversation_id: conversationId }) });
  if (!response.body) throw new Error("无流式响应");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n"); buffer = chunks.pop() || "";
    chunks.forEach(chunk => { const line = chunk.split("\n").find(x => x.startsWith("data: ")); if (line) onEvent(JSON.parse(line.slice(6))); });
  }
}

export async function confirmAction(id: number) { return fetch(`${API}/api/v1/actions/${id}/confirm`, { method: "POST" }); }

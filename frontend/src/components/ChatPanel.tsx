import { useState } from "react";

export function ChatPanel({ onSend, messages, loading }: { onSend: (text: string) => void; messages: { role: string; content: string }[]; loading: boolean }) {
  const [input, setInput] = useState("");
  const submit = () => { if (input.trim()) { onSend(input.trim()); setInput(""); } };
  return <div className="panel chat"><h2>对话</h2><div className="messages">{messages.map((m, i) => <div className={`bubble ${m.role}`} key={i}>{m.content}</div>)}</div><div className="composer"><input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && submit()} placeholder="告诉我你想安排什么…"/><button onClick={submit} disabled={loading}>发送</button></div></div>;
}


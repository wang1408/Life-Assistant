export function WeatherCard({ weather }: { weather: any }) { return <div className="row"><span>天气</span><small>{weather?.message || weather?.now?.text || "暂无天气"}</small></div>; }


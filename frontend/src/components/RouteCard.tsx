export function RouteCard({ route }: { route: any }) { return <div className="row"><span>路线</span><small>{route?.message || route?.duration || "暂无路线"}</small></div>; }


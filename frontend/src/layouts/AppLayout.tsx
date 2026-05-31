import { Outlet, Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"

export default function MainLayout() {
  const { user, login, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold">W</div>
            <h1 className="text-xl font-bold text-slate-800">名人堂百科</h1>
          </div>

          <nav className="space-x-2">
            <Button variant="ghost" asChild>
              <Link to="/">首页检索</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link to="/profile">我的履历</Link>
            </Button>
            {user ? (
              <Button variant="outline" onClick={logout}>
                {user.username}，退出
              </Button>
            ) : (
              <Button onClick={login}>登录</Button>
            )}
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}

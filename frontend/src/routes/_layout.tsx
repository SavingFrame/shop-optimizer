import { createFileRoute, Link, Outlet } from "@tanstack/react-router"
import {
  LogIn,
  LogOut,
  PackageSearch,
  ReceiptText,
  Settings,
  ShoppingBasket,
  UserPlus,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
})

function Layout() {
  const { logout, user } = useAuth()
  const loggedIn = isLoggedIn()

  return (
    <div className="min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.18),transparent_34rem),radial-gradient(circle_at_top_right,rgba(132,204,22,0.12),transparent_30rem)]" />
      <header className="sticky top-0 z-20 border-b border-border/60 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <ShoppingBasket className="size-5" />
            </span>
            <div>
              <p className="font-semibold tracking-tight">Shop Optimizer</p>
              <p className="text-xs text-muted-foreground">
                Croatian grocery intelligence
              </p>
            </div>
          </Link>

          <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
            <Link className="transition hover:text-foreground" to="/products">
              Products
            </Link>
            <a className="transition hover:text-foreground" href="#basket">
              Basket
            </a>
            <Link className="transition hover:text-foreground" to="/receipts">
              Receipts
            </Link>
          </nav>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/products">
                <PackageSearch className="size-4" />
                Browse products
              </Link>
            </Button>
            <Button size="sm" className="hidden sm:inline-flex" asChild>
              <Link to="/receipts">
                <ReceiptText className="size-4" />
                Receipt upload
              </Link>
            </Button>
            {loggedIn ? (
              <>
                {user?.email && (
                  <span className="hidden max-w-48 truncate text-sm text-muted-foreground lg:inline">
                    {user.email}
                  </span>
                )}
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/settings">
                    <Settings className="size-4" />
                    Settings
                  </Link>
                </Button>
                <Button variant="outline" size="sm" onClick={logout}>
                  <LogOut className="size-4" />
                  Log out
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/login">
                    <LogIn className="size-4" />
                    Log in
                  </Link>
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <Link to="/signup">
                    <UserPlus className="size-4" />
                    Sign up
                  </Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

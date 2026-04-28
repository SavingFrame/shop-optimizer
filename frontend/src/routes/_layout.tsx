import { createFileRoute, Link, Outlet } from "@tanstack/react-router"
import { PackageSearch, ReceiptText, ShoppingBasket } from "lucide-react"

import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/_layout")({
  component: Layout,
})

function Layout() {
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
            <a className="transition hover:text-foreground" href="#receipts">
              Receipts
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/products">
                <PackageSearch className="size-4" />
                Browse products
              </Link>
            </Button>
            <Button size="sm" className="hidden sm:inline-flex" asChild>
              <a href="#receipts">
                <ReceiptText className="size-4" />
                Receipt upload
              </a>
            </Button>
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

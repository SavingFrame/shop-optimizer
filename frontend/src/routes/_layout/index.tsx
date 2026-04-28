import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowDownRight,
  ArrowUpRight,
  BadgeEuro,
  Clock3,
  PackageOpen,
  ReceiptText,
  Search,
  ShoppingCart,
  Sparkles,
  Store,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const basketItems = [
  { name: "Milk 2.8%", quantity: "2 L", bestShop: "Konzum", price: "2.58 €" },
  { name: "Eggs M", quantity: "10 pcs", bestShop: "Lidl", price: "2.39 €" },
  { name: "Rice", quantity: "1 kg", bestShop: "Kaufland", price: "1.79 €" },
  { name: "Coffee", quantity: "250 g", bestShop: "Lidl", price: "3.49 €" },
]

const shopTotals = [
  { shop: "Lidl", total: "18.24 €", status: "Cheapest", delta: "Save 2.16 €" },
  {
    shop: "Kaufland",
    total: "19.10 €",
    status: "Good match",
    delta: "Save 1.30 €",
  },
  { shop: "Konzum", total: "20.40 €", status: "Complete", delta: "Baseline" },
]

const productResults = [
  {
    name: "Milk 2.8%",
    category: "Dairy",
    unit: "1 L",
    bestPrice: "1.29 €",
    shop: "Konzum",
    change: "-8%",
    trend: "down",
  },
  {
    name: "Coffee ground",
    category: "Pantry",
    unit: "250 g",
    bestPrice: "3.49 €",
    shop: "Lidl",
    change: "+12%",
    trend: "up",
  },
  {
    name: "Eggs M",
    category: "Fresh food",
    unit: "10 pcs",
    bestPrice: "2.39 €",
    shop: "Lidl",
    change: "-4%",
    trend: "down",
  },
]

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Shop Optimizer dashboard",
      },
      {
        name: "description",
        content:
          "Find Croatian grocery products, compare shop prices, and optimize baskets.",
      },
    ],
  }),
})

function Dashboard() {
  return (
    <div className="space-y-8 pb-12">
      <section className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr] lg:items-stretch">
        <Card className="relative overflow-hidden border-primary/20 bg-card/80 shadow-2xl shadow-primary/5">
          <div className="absolute right-0 top-0 h-56 w-56 rounded-full bg-primary/15 blur-3xl" />
          <CardHeader className="relative gap-5 p-6 sm:p-8">
            <Badge variant="secondary" className="w-fit gap-2 px-3 py-1">
              <Sparkles className="size-3.5 text-primary" />
              Dashboard preview
            </Badge>
            <div className="max-w-2xl space-y-4">
              <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
                Find any product and compare prices before you shop.
              </h1>
              <p className="text-base leading-7 text-muted-foreground sm:text-lg">
                Search normalized grocery products, open product details, and
                see the best current price across Croatian shops.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button size="lg" asChild>
                <Link to="/products">
                  <Search className="size-4" />
                  Browse products
                </Link>
              </Button>
              <Button variant="outline" size="lg" asChild>
                <a href="#basket">
                  <ShoppingCart className="size-4" />
                  Compare basket
                </a>
              </Button>
            </div>
          </CardHeader>
        </Card>

        <Card id="products" className="border-border/70 bg-card/70 shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Search className="size-5 text-primary" />
              Product search
            </CardTitle>
            <CardDescription>
              Find normalized products, then open a detail page with shop prices
              and history.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border bg-background/70 p-4">
              <p className="text-sm text-muted-foreground">Search products</p>
              <p className="mt-1 text-xl font-medium">
                milk, eggs, bread, rice...
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <MetricCard
                icon={PackageOpen}
                label="Product catalog"
                value="Core"
              />
              <MetricCard icon={Store} label="Shop prices" value="Compared" />
              <MetricCard
                icon={BadgeEuro}
                label="Best product price"
                value="1.29 €/L"
              />
              <MetricCard icon={Clock3} label="Updated" value="Today" />
            </div>
          </CardContent>
        </Card>
      </section>

      <section id="basket" className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card className="bg-card/80">
          <CardHeader>
            <CardTitle>Basket builder</CardTitle>
            <CardDescription>
              A first version of the core workflow, using sample products until
              the API is ready.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {basketItems.map((item) => (
              <div
                className="flex items-center justify-between gap-4 rounded-2xl border bg-background/60 p-4"
                key={item.name}
              >
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.quantity}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{item.price}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.bestShop}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card id="shops" className="bg-card/80">
          <CardHeader>
            <CardTitle>Cheapest shop comparison</CardTitle>
            <CardDescription>
              Compare the full basket total across shops and expose expected
              savings.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {shopTotals.map((shop, index) => (
              <div
                className="rounded-2xl border bg-background/60 p-4"
                key={shop.shop}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex size-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{shop.shop}</p>
                      <p className="text-sm text-muted-foreground">
                        {shop.status}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-semibold">{shop.total}</p>
                    <p className="text-sm text-primary">{shop.delta}</p>
                  </div>
                </div>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${92 - index * 14}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Product detail preview</CardTitle>
            <CardDescription>
              Each result should lead to a product page with unit price, shop
              availability, and recent changes.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {productResults.map((product) => {
              const isDown = product.trend === "down"
              const Icon = isDown ? ArrowDownRight : ArrowUpRight

              return (
                <div
                  className="grid gap-4 rounded-2xl border bg-background/60 p-4 sm:grid-cols-[1fr_auto] sm:items-center"
                  key={product.name}
                >
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium">{product.name}</p>
                      <Badge variant="secondary">{product.category}</Badge>
                      <Badge variant="outline">{product.unit}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Best at {product.shop}. Open details to compare all shops
                      and view price history.
                    </p>
                  </div>
                  <div className="flex items-center justify-between gap-5 sm:justify-end">
                    <div className="text-right">
                      <p className="text-xl font-semibold">
                        {product.bestPrice}
                      </p>
                      <p
                        className={
                          isDown
                            ? "text-sm text-primary"
                            : "text-sm text-destructive"
                        }
                      >
                        {product.change} recently
                      </p>
                    </div>
                    <Icon
                      className={
                        isDown
                          ? "size-5 text-primary"
                          : "size-5 text-destructive"
                      }
                    />
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>

        <Card
          id="receipts"
          className="border-primary/20 bg-primary text-primary-foreground"
        >
          <CardHeader>
            <CardTitle>Next feature</CardTitle>
            <CardDescription className="text-primary-foreground/75">
              Receipt upload can become the bridge from past shopping to today's
              comparison.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-2xl bg-primary-foreground/10 p-4">
              <ReceiptText className="mb-4 size-8" />
              <p className="text-sm leading-6 text-primary-foreground/85">
                Upload a bill, extract products and quantities, then compare the
                same basket against current shop prices.
              </p>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

type MetricCardProps = {
  icon: typeof Store
  label: string
  value: string
}

function MetricCard({ icon: Icon, label, value }: MetricCardProps) {
  return (
    <div className="rounded-2xl border bg-background/60 p-4">
      <Icon className="mb-3 size-5 text-primary" />
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  )
}

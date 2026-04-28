import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Barcode,
  ImageIcon,
  PackageOpen,
  Ruler,
  Store,
} from "lucide-react"
import { useState } from "react"

import { ProductsService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export const Route = createFileRoute("/_layout/products/$productId")({
  component: ProductDetailPage,
  head: () => ({
    meta: [
      {
        title: "Product details - Shop Optimizer",
      },
    ],
  }),
})

function ProductDetailPage() {
  const { productId } = Route.useParams()

  const { data, isPending, isError } = useQuery({
    queryKey: ["products"],
    queryFn: () => ProductsService.readProducts({ limit: 100, skip: 0 }),
  })

  const product = data?.data.find((item) => item.id === productId)

  if (isPending) {
    return (
      <div className="space-y-6 pb-12">
        <div className="h-10 w-36 animate-pulse rounded-full bg-card" />
        <div className="h-96 animate-pulse rounded-3xl border bg-card/70" />
      </div>
    )
  }

  if (isError) {
    return (
      <ProductMessage
        title="Could not load product"
        description="Check that the backend is running and the generated API client points to the correct URL."
      />
    )
  }

  if (!product) {
    return (
      <ProductMessage
        title="Product not found"
        description="This product is not in the current loaded product page. A dedicated backend detail endpoint can remove this limitation later."
      />
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/products">
          <ArrowLeft className="size-4" />
          Back to products
        </Link>
      </Button>

      <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <Card className="overflow-hidden bg-card/80">
          <ProductImage imageUrl={product.image_url} name={product.name} />
        </Card>

        <Card className="bg-card/80">
          <CardHeader className="gap-4 p-6 sm:p-8">
            <div className="flex flex-wrap gap-2">
              {product.category && (
                <Badge variant="secondary">{product.category}</Badge>
              )}
              {product.brand && (
                <Badge variant="outline">{product.brand}</Badge>
              )}
            </div>
            <div className="space-y-3">
              <CardTitle className="text-3xl leading-tight sm:text-5xl">
                {product.name}
              </CardTitle>
              <CardDescription className="text-base leading-7">
                Product detail page placeholder. Prices, shop availability, and
                price history can be connected here when those endpoints are
                ready.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 p-6 pt-0 sm:grid-cols-2 sm:p-8 sm:pt-0">
            <InfoTile
              icon={PackageOpen}
              label="Quantity"
              value={product.net_quantity}
            />
            <InfoTile
              icon={Ruler}
              label="Unit"
              value={product.unit_of_measure}
            />
            <InfoTile icon={Barcode} label="Barcode" value={product.barcode} />
            <InfoTile icon={Store} label="Shop prices" value="Coming soon" />
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Price comparison</CardTitle>
            <CardDescription>
              This section will show every shop price for this product.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PlaceholderRows labels={["Konzum", "Lidl", "Kaufland"]} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Price history</CardTitle>
            <CardDescription>
              This section will become a chart when history data is available.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex h-48 items-end gap-3 rounded-2xl border bg-background/60 p-4">
              {[44, 68, 52, 80, 64, 72, 58].map((height, index) => (
                <div
                  className="flex-1 rounded-t-xl bg-primary/70"
                  key={index}
                  style={{ height: `${height}%` }}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

type ProductImageProps = {
  imageUrl?: string | null
  name: string
}

function ProductImage({ imageUrl, name }: ProductImageProps) {
  const [hasError, setHasError] = useState(false)

  if (imageUrl && !hasError) {
    return (
      <div className="flex aspect-square items-center justify-center bg-muted/40">
        <img
          alt={name}
          className="h-full w-full object-contain p-8"
          loading="lazy"
          onError={() => setHasError(true)}
          src={imageUrl}
        />
      </div>
    )
  }

  return (
    <div className="flex aspect-square items-center justify-center bg-gradient-to-br from-primary/20 via-primary/10 to-background">
      <div className="flex size-28 items-center justify-center rounded-[2rem] bg-background/80 text-primary shadow-xl shadow-primary/10">
        <ImageIcon className="size-12" />
      </div>
    </div>
  )
}

type InfoTileProps = {
  icon: typeof PackageOpen
  label: string
  value?: string | null
}

function InfoTile({ icon: Icon, label, value }: InfoTileProps) {
  return (
    <div className="rounded-2xl border bg-background/60 p-4">
      <Icon className="mb-3 size-5 text-primary" />
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 font-semibold">{value || "Not available"}</p>
    </div>
  )
}

type PlaceholderRowsProps = {
  labels: Array<string>
}

function PlaceholderRows({ labels }: PlaceholderRowsProps) {
  return (
    <div className="space-y-3">
      {labels.map((label, index) => (
        <div
          className="flex items-center justify-between rounded-2xl border bg-background/60 p-4"
          key={label}
        >
          <div>
            <p className="font-medium">{label}</p>
            <p className="text-sm text-muted-foreground">
              Price endpoint pending
            </p>
          </div>
          <Badge variant={index === 0 ? "default" : "secondary"}>
            Coming soon
          </Badge>
        </div>
      ))}
    </div>
  )
}

type ProductMessageProps = {
  title: string
  description: string
}

function ProductMessage({ title, description }: ProductMessageProps) {
  return (
    <div className="space-y-6 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/products">
          <ArrowLeft className="size-4" />
          Back to products
        </Link>
      </Button>
      <Card>
        <CardContent className="flex min-h-64 flex-col items-center justify-center gap-3 text-center">
          <PackageOpen className="size-10 text-muted-foreground" />
          <div>
            <p className="font-medium">{title}</p>
            <p className="max-w-md text-sm text-muted-foreground">
              {description}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

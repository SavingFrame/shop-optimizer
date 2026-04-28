import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  Barcode,
  ChevronRight,
  ImageIcon,
  PackageSearch,
  Search,
} from "lucide-react"
import { useMemo, useState } from "react"

import { type ProductPublic, ProductsService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/_layout/products")({
  component: ProductsPage,
  head: () => ({
    meta: [
      {
        title: "Products - Shop Optimizer",
      },
      {
        name: "description",
        content: "Search Croatian grocery products and compare shop prices.",
      },
    ],
  }),
})

function ProductsPage() {
  const [search, setSearch] = useState("")

  const { data, isPending, isError } = useQuery({
    queryKey: ["products"],
    queryFn: () => ProductsService.readProducts({ limit: 100, skip: 0 }),
  })

  const products = data?.data ?? []
  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase()

    if (!query) {
      return products
    }

    return products.filter((product) =>
      [
        product.name,
        product.brand,
        product.category,
        product.barcode,
        product.net_quantity,
        product.unit_of_measure,
      ]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(query)),
    )
  }, [products, search])

  return (
    <div className="space-y-8 pb-12">
      <section className="grid gap-6 lg:grid-cols-[1fr_0.7fr] lg:items-end">
        <div className="space-y-4">
          <Badge variant="secondary" className="gap-2 px-3 py-1">
            <PackageSearch className="size-3.5 text-primary" />
            Product catalog
          </Badge>
          <div className="space-y-3">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Search products
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground">
              Browse normalized grocery products. Search runs locally for now,
              and can move to the backend when the API supports it.
            </p>
          </div>
        </div>

        <Card className="bg-card/80">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="h-12 rounded-2xl pl-10 text-base"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by name, brand, category, barcode..."
                value={search}
              />
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <SummaryCard
          label="Total products"
          value={(data?.count ?? 0).toString()}
        />
        <SummaryCard
          label="Matching search"
          value={filteredProducts.length.toString()}
        />
        <SummaryCard label="Search mode" value="Local" />
      </section>

      {isPending && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              className="h-56 animate-pulse rounded-3xl border bg-card/70"
              key={index}
            />
          ))}
        </div>
      )}

      {isError && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardHeader>
            <CardTitle>Could not load products</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Check that the backend is running and that the generated client uses
            the correct API URL.
          </CardContent>
        </Card>
      )}

      {!isPending && !isError && filteredProducts.length === 0 && (
        <Card>
          <CardContent className="flex min-h-48 flex-col items-center justify-center gap-3 text-center">
            <PackageSearch className="size-10 text-muted-foreground" />
            <div>
              <p className="font-medium">No products found</p>
              <p className="text-sm text-muted-foreground">
                Try a different product name, brand, category, or barcode.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {!isPending && !isError && filteredProducts.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}

type SummaryCardProps = {
  label: string
  value: string
}

function SummaryCard({ label, value }: SummaryCardProps) {
  return (
    <Card className="bg-card/70">
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      </CardContent>
    </Card>
  )
}

type ProductCardProps = {
  product: ProductPublic
}

function ProductCard({ product }: ProductCardProps) {
  return (
    <Link
      to="/products/$productId"
      params={{ productId: product.id }}
      className="group rounded-3xl outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      <Card className="h-full overflow-hidden bg-card/80 transition duration-200 group-hover:-translate-y-1 group-hover:border-primary/40 group-hover:shadow-xl group-hover:shadow-primary/5">
        <ProductImage imageUrl={product.image_url} name={product.name} />
        <CardContent className="space-y-4 p-5">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {product.category && (
                <Badge variant="secondary">{product.category}</Badge>
              )}
              {product.brand && (
                <Badge variant="outline">{product.brand}</Badge>
              )}
            </div>
            <h2 className="line-clamp-2 text-lg font-semibold leading-snug">
              {product.name}
            </h2>
          </div>

          <div className="space-y-2 text-sm text-muted-foreground">
            <ProductMeta label="Quantity" value={product.net_quantity} />
            <ProductMeta label="Unit" value={product.unit_of_measure} />
            {product.barcode && (
              <div className="flex items-center gap-2">
                <Barcode className="size-4" />
                <span className="truncate">{product.barcode}</span>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between border-t pt-4 text-sm font-medium text-primary">
            <span>Open details</span>
            <ChevronRight className="size-4 transition group-hover:translate-x-1" />
          </div>
        </CardContent>
      </Card>
    </Link>
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
      <div className="flex h-36 items-center justify-center bg-muted/40">
        <img
          alt={name}
          className="h-full w-full object-contain p-4 transition duration-200 group-hover:scale-105"
          loading="lazy"
          onError={() => setHasError(true)}
          src={imageUrl}
        />
      </div>
    )
  }

  return (
    <div className="flex h-36 items-center justify-center bg-gradient-to-br from-primary/20 via-primary/10 to-background">
      <div className="flex size-20 items-center justify-center rounded-3xl bg-background/80 text-primary shadow-lg shadow-primary/10">
        <ImageIcon className="size-9" />
      </div>
    </div>
  )
}

type ProductMetaProps = {
  label: string
  value?: string | null
}

function ProductMeta({ label, value }: ProductMetaProps) {
  if (!value) {
    return null
  }

  return (
    <div className="flex items-center justify-between gap-3">
      <span>{label}</span>
      <span className="truncate font-medium text-foreground">{value}</span>
    </div>
  )
}

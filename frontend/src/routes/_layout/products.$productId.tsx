import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Barcode,
  CalendarDays,
  ImageIcon,
  type LucideIcon,
  PackageOpen,
  Ruler,
  Store,
  Tags,
} from "lucide-react"
import { useMemo, useState } from "react"

import {
  type ProductPublic,
  ProductsService,
  type RetailerPriceObservationSummary,
} from "@/client"
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

  const productQuery = useQuery({
    queryKey: ["products", productId],
    queryFn: () => ProductsService.readProduct({ productId }),
  })

  const pricesQuery = useQuery({
    queryKey: ["products", productId, "price-observations", "grouped"],
    queryFn: () =>
      ProductsService.groupedProductPriceObservations({ productId }),
  })

  const product = productQuery.data
  const prices = pricesQuery.data ?? []
  const lowestPrice = useMemo(() => findLowestPrice(prices), [prices])

  if (productQuery.isPending) {
    return (
      <div className="space-y-6 pb-12">
        <div className="h-10 w-36 animate-pulse rounded-full bg-card" />
        <div className="h-96 animate-pulse rounded-3xl border bg-card/70" />
      </div>
    )
  }

  if (productQuery.isError || !product) {
    return (
      <ProductMessage
        title="Could not load product"
        description="Check that the product exists and that the backend is running."
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

      <ProductHero product={product} pricesCount={prices.length} />

      <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <Card>
          <CardHeader>
            <CardTitle>Shop prices</CardTitle>
            <CardDescription>
              Retailer prices grouped from the latest available observations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PriceObservations
              isError={pricesQuery.isError}
              isPending={pricesQuery.isPending}
              observations={prices}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Price summary</CardTitle>
            <CardDescription>
              A quick view of available shop data for this product.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <InfoTile
              icon={Store}
              label="Observed retailers"
              value={
                pricesQuery.isPending ? "Loading" : prices.length.toString()
              }
            />
            <InfoTile
              icon={Tags}
              label="Lowest retail price"
              value={lowestPrice ? formatCurrency(lowestPrice) : undefined}
            />
            <InfoTile
              icon={CalendarDays}
              label="Latest observation"
              value={formatLatestDate(prices)}
            />
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

type ProductHeroProps = {
  pricesCount: number
  product: ProductPublic
}

function ProductHero({ pricesCount, product }: ProductHeroProps) {
  return (
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
            {product.brand && <Badge variant="outline">{product.brand}</Badge>}
          </div>
          <div className="space-y-3">
            <CardTitle className="text-3xl leading-tight sm:text-5xl">
              {product.name}
            </CardTitle>
            <CardDescription className="text-base leading-7">
              Compare current shop price observations for this normalized
              product.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 p-6 pt-0 sm:grid-cols-2 sm:p-8 sm:pt-0">
          <InfoTile
            icon={PackageOpen}
            label="Quantity"
            value={product.net_quantity}
          />
          <InfoTile icon={Ruler} label="Unit" value={product.unit_of_measure} />
          <InfoTile icon={Barcode} label="Barcode" value={product.barcode} />
          <InfoTile
            icon={Store}
            label="Retailer prices"
            value={pricesCount.toString()}
          />
        </CardContent>
      </Card>
    </section>
  )
}

type PriceObservationsProps = {
  isError: boolean
  isPending: boolean
  observations: Array<RetailerPriceObservationSummary>
}

function PriceObservations({
  isError,
  isPending,
  observations,
}: PriceObservationsProps) {
  const sortedObservations = useMemo(
    () => [...observations].sort(compareObservations),
    [observations],
  )

  if (isPending) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            className="h-24 animate-pulse rounded-2xl border bg-background/60"
            key={index}
          />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
        Could not load product price observations.
      </div>
    )
  }

  if (sortedObservations.length === 0) {
    return (
      <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border bg-background/60 p-6 text-center">
        <Store className="size-10 text-muted-foreground" />
        <div>
          <p className="font-medium">No price observations yet</p>
          <p className="text-sm text-muted-foreground">
            This product does not have imported shop prices.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {sortedObservations.map((observation) => (
        <PriceObservationRow
          key={`${observation.retailer.id}-${observation.observed_date}`}
          observation={observation}
        />
      ))}
    </div>
  )
}

type PriceObservationRowProps = {
  observation: RetailerPriceObservationSummary
}

function PriceObservationRow({ observation }: PriceObservationRowProps) {
  const retailPrice = getAveragePrice(observation)
  const retailPriceRange = formatPriceRange(
    getMinPrice(observation),
    getMaxPrice(observation),
  )
  const unitPriceRange = formatPriceRange(
    observation.min_unit_price_eur,
    observation.max_unit_price_eur,
  )

  return (
    <div className="rounded-2xl border bg-background/60 p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-semibold">{observation.retailer.name}</p>
            <Badge variant="secondary">{observation.store_count} stores</Badge>
            {(observation.has_store_price_variance ||
              observation.has_store_special_sale_price_variance) && (
              <Badge variant="outline">Price varies by store</Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            <span>{observation.observed_date}</span>
            <span>{observation.observation_count} observations</span>
          </div>
        </div>

        <div className="shrink-0 text-left sm:text-right">
          <p className="text-2xl font-semibold tracking-tight">
            {retailPrice ? formatCurrency(retailPrice) : "No retail price"}
          </p>
          <p className="text-sm text-muted-foreground">
            {formatCurrency(observation.average_unit_price_eur)} avg per unit
          </p>
          <div className="mt-2 flex flex-col gap-1 text-xs text-muted-foreground">
            {retailPriceRange && <span>Price range {retailPriceRange}</span>}
            {unitPriceRange && <span>Unit range {unitPriceRange}</span>}
          </div>
          {observation.average_special_sale_price_eur && (
            <Badge className="mt-2" variant="outline">
              Avg sale{" "}
              {formatCurrency(observation.average_special_sale_price_eur)}
            </Badge>
          )}
        </div>
      </div>
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
  icon: LucideIcon
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

function compareObservations(
  first: RetailerPriceObservationSummary,
  second: RetailerPriceObservationSummary,
) {
  const firstPrice = Number(getAveragePrice(first) ?? Number.POSITIVE_INFINITY)
  const secondPrice = Number(
    getAveragePrice(second) ?? Number.POSITIVE_INFINITY,
  )

  if (firstPrice !== secondPrice) {
    return firstPrice - secondPrice
  }

  return second.observed_date.localeCompare(first.observed_date)
}

function findLowestPrice(observations: Array<RetailerPriceObservationSummary>) {
  return observations
    .map(getMinPrice)
    .filter((price): price is string => Boolean(price))
    .sort((first, second) => Number(first) - Number(second))[0]
}

function formatCurrency(value: string) {
  return new Intl.NumberFormat("hr-HR", {
    currency: "EUR",
    style: "currency",
  }).format(Number(value))
}

function formatLatestDate(
  observations: Array<RetailerPriceObservationSummary>,
) {
  const latestDate = observations
    .map((observation) => observation.observed_date)
    .sort((first, second) => second.localeCompare(first))[0]

  return latestDate || undefined
}

function getAveragePrice(observation: RetailerPriceObservationSummary) {
  return (
    observation.average_special_sale_price_eur ??
    observation.average_retail_price_eur
  )
}

function getMinPrice(observation: RetailerPriceObservationSummary) {
  return (
    observation.min_special_sale_price_eur ?? observation.min_retail_price_eur
  )
}

function getMaxPrice(observation: RetailerPriceObservationSummary) {
  return (
    observation.max_special_sale_price_eur ?? observation.max_retail_price_eur
  )
}

function formatPriceRange(minPrice?: string | null, maxPrice?: string | null) {
  if (!minPrice || !maxPrice || minPrice === maxPrice) {
    return undefined
  }

  return `${formatCurrency(minPrice)} to ${formatCurrency(maxPrice)}`
}

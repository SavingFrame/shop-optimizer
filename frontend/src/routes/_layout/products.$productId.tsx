import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Barcode,
  CalendarDays,
  ImageIcon,
  type LucideIcon,
  PackageOpen,
  PackageSearch,
  Store,
  Tags,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import {
  type ProductPublic,
  ProductsService,
  type RetailerDailyRetailPriceHistoryPoint,
  type RetailerPriceObservationSummary,
  type SimilarProductPublic,
} from "@/client"
import { AddProductToListDialog } from "@/components/ProductLists/AddProductToListDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const LAST_PRODUCTS_PATH_STORAGE_KEY = "products:last-path"

type ProductsBackSearch = {
  page?: number
  q?: string
}

export const Route = createFileRoute("/_layout/products/$productId")({
  component: ProductDetailPage,
  head: () => ({
    meta: [
      {
        title: "Product details - Cjenolovac",
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

  const priceHistoryQuery = useQuery({
    queryKey: ["products", productId, "price-history", "retail", "chart"],
    queryFn: () =>
      ProductsService.productDailyRetailPriceHistoryChart({ productId }),
  })

  const similarProductsQuery = useQuery({
    queryKey: ["products", productId, "similar"],
    queryFn: () =>
      ProductsService.readSimilarProducts({ productId, limit: 12 }),
  })

  const product = productQuery.data
  const prices = pricesQuery.data ?? []
  const lowestPrice = useMemo(() => findLowestPrice(prices), [prices])
  const priceSpread = useMemo(
    () => formatObservationsPriceSpread(prices),
    [prices],
  )
  const lowestPriceRetailer = lowestPrice?.retailer.name
  const productsBackSearch = useProductsBackSearch()

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
        productsBackSearch={productsBackSearch}
      />
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/products" search={productsBackSearch}>
          <ArrowLeft className="size-4" />
          Back to products
        </Link>
      </Button>

      <ProductHero
        currentPrice={lowestPrice?.price}
        isPricePending={pricesQuery.isPending}
        latestObservationDate={formatLatestDate(prices)}
        lowestObservation={lowestPrice?.observation}
        lowestPriceRetailer={lowestPriceRetailer}
        pricesCount={prices.length}
        product={product}
      />

      <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <Card>
          <CardHeader>
            <CardTitle>Shop prices</CardTitle>
            <CardDescription>
              Current retailer prices from the latest available observations.
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
            <InfoTile icon={Tags} label="Price spread" value={priceSpread} />
            <InfoTile
              icon={CalendarDays}
              label="Latest observation"
              value={formatLatestDate(prices)}
            />
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Price history</CardTitle>
          <CardDescription>
            Daily average price by retailer. Hover a point to see the recorded
            min and max range for that day.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PriceHistoryChart
            isError={priceHistoryQuery.isError}
            isPending={priceHistoryQuery.isPending}
            points={priceHistoryQuery.data ?? []}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Similar products</CardTitle>
          <CardDescription>
            Suggested alternatives from the catalog when the exact barcode is
            not enough for comparing retailers.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SimilarProducts
            isError={similarProductsQuery.isError}
            isPending={similarProductsQuery.isPending}
            products={similarProductsQuery.data ?? []}
          />
        </CardContent>
      </Card>
    </div>
  )
}

type ProductHeroProps = {
  currentPrice?: string
  isPricePending: boolean
  latestObservationDate?: string
  lowestObservation?: RetailerPriceObservationSummary
  lowestPriceRetailer?: string
  pricesCount: number
  product: ProductPublic
}

function ProductHero({
  currentPrice,
  isPricePending,
  latestObservationDate,
  lowestObservation,
  lowestPriceRetailer,
  pricesCount,
  product,
}: ProductHeroProps) {
  const formattedCurrentPrice = currentPrice
    ? formatCurrency(currentPrice)
    : undefined

  return (
    <Card className="overflow-hidden bg-card/80">
      <div className="grid gap-0 lg:grid-cols-[18rem_1fr] xl:grid-cols-[22rem_1fr]">
        <ProductImage imageUrl={product.image_url} name={product.name} />

        <div className="flex min-w-0 flex-col">
          <CardHeader className="gap-4 p-5 sm:p-6">
            <div className="flex flex-wrap gap-2">
              {product.category && (
                <Badge variant="secondary">{product.category}</Badge>
              )}
              {product.brand && (
                <Badge variant="outline">{product.brand}</Badge>
              )}
            </div>
            <div className="space-y-2">
              <CardTitle className="text-2xl leading-tight sm:text-4xl">
                {product.name}
              </CardTitle>
              <CardDescription className="text-sm sm:text-base">
                Latest observed price and product details.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 p-5 pt-0 sm:p-6 sm:pt-0">
            <div className="grid gap-3 md:grid-cols-[1.15fr_1fr]">
              <CurrentPriceTile
                isPending={isPricePending}
                latestObservationDate={latestObservationDate}
                observation={lowestObservation}
                price={formattedCurrentPrice}
                retailerName={lowestPriceRetailer}
                retailersCount={pricesCount}
              />
              <div className="grid gap-3 sm:grid-cols-2">
                <InfoTile
                  icon={PackageOpen}
                  label="Package"
                  value={formatPackageSize(product)}
                />
                <InfoTile
                  icon={Barcode}
                  label="Barcode"
                  value={product.barcode}
                />
                <InfoTile
                  icon={Store}
                  label="Retailer prices"
                  value={pricesCount.toString()}
                />
              </div>
            </div>
            <AddProductToListDialog
              productId={product.id}
              productName={product.name}
            />
          </CardContent>
        </div>
      </div>
    </Card>
  )
}

type SimilarProductsProps = {
  isError: boolean
  isPending: boolean
  products: Array<SimilarProductPublic>
}

function SimilarProducts({
  isError,
  isPending,
  products,
}: SimilarProductsProps) {
  if (isPending) {
    return (
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            className="h-40 animate-pulse rounded-2xl border bg-background/60"
            key={index}
          />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
        Could not load similar products.
      </div>
    )
  }

  if (products.length === 0) {
    return (
      <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border bg-background/60 p-6 text-center">
        <PackageSearch className="size-10 text-muted-foreground" />
        <div>
          <p className="font-medium">No similar products found</p>
          <p className="text-sm text-muted-foreground">
            Try searching the product catalog manually for alternatives.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {products.map((candidate) => (
        <SimilarProductCard candidate={candidate} key={candidate.product.id} />
      ))}
    </div>
  )
}

type SimilarProductCardProps = {
  candidate: SimilarProductPublic
}

function SimilarProductCard({ candidate }: SimilarProductCardProps) {
  const retailers = candidate.retailers
    .map((retailer) => retailer.name)
    .join(", ")

  return (
    <Link
      className="flex gap-4 rounded-2xl border bg-background/60 p-4 transition-colors hover:border-primary/40 hover:bg-background"
      params={{ productId: candidate.product.id }}
      to="/products/$productId"
    >
      <SimilarProductImage
        imageUrl={candidate.product.image_url}
        name={candidate.product.name}
      />
      <div className="min-w-0 flex-1 space-y-3">
        <div className="flex flex-wrap gap-2">
          {candidate.product.category && (
            <Badge variant="secondary">{candidate.product.category}</Badge>
          )}
          {candidate.product.brand && (
            <Badge variant="outline">{candidate.product.brand}</Badge>
          )}
        </div>
        <div className="space-y-1">
          <p className="line-clamp-2 font-semibold">{candidate.product.name}</p>
          <p className="line-clamp-1 text-sm text-muted-foreground">
            {retailers || "No retailer data"}
          </p>
        </div>
        <div className="text-sm">
          <span className="text-muted-foreground">Latest price </span>
          <span className="font-semibold">
            {candidate.latest_price_eur
              ? formatCurrency(candidate.latest_price_eur)
              : "Not available"}
          </span>
        </div>
      </div>
    </Link>
  )
}

type SimilarProductImageProps = {
  imageUrl?: string | null
  name: string
}

function SimilarProductImage({ imageUrl, name }: SimilarProductImageProps) {
  const [hasError, setHasError] = useState(false)

  if (imageUrl && !hasError) {
    return (
      <div className="flex size-24 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-muted/40">
        <img
          alt={name}
          className="h-full w-full object-contain p-2"
          loading="lazy"
          onError={() => setHasError(true)}
          src={imageUrl}
        />
      </div>
    )
  }

  return (
    <div className="flex size-24 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 via-primary/10 to-background text-primary">
      <ImageIcon className="size-8" />
    </div>
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
      {sortedObservations.map((observation, index) => (
        <PriceObservationRow
          isBestPrice={index === 0}
          key={`${observation.retailer.id}-${observation.observed_date}`}
          observation={observation}
          priceDelta={formatPriceDeltaFromBest(
            getAveragePrice(observation),
            getAveragePrice(sortedObservations[0]),
          )}
        />
      ))}
    </div>
  )
}

type PriceHistoryChartProps = {
  isError: boolean
  isPending: boolean
  points: Array<RetailerDailyRetailPriceHistoryPoint>
}

type PriceHistoryChartData = {
  rows: Array<PriceHistoryDatum>
  series: Array<PriceHistorySeries>
}

type PriceHistoryDatum = {
  observed_date: string
} & Record<string, boolean | number | string | null>

type PriceHistorySeries = {
  color: string
  dataKey: string
  id: string
  maxKey: string
  minKey: string
  name: string
}

type PriceHistoryTooltipPayload = {
  color?: string
  dataKey?: string | number
  name?: string
  payload?: PriceHistoryDatum
  value?: number | string | null
}

type PriceHistoryTooltipProps = {
  active?: boolean
  label?: string
  payload?: Array<PriceHistoryTooltipPayload>
}

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
]

function PriceHistoryChart({
  isError,
  isPending,
  points,
}: PriceHistoryChartProps) {
  const chartData = useMemo(() => buildPriceHistoryChartData(points), [points])
  const priceDomain = useMemo(
    () => getPriceHistoryDomain(chartData.rows, chartData.series),
    [chartData],
  )

  if (isPending) {
    return <div className="h-80 animate-pulse rounded-2xl bg-background/60" />
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
        Could not load retail price history.
      </div>
    )
  }

  if (chartData.rows.length === 0 || chartData.series.length === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center gap-3 rounded-2xl border bg-background/60 p-6 text-center">
        <CalendarDays className="size-10 text-muted-foreground" />
        <div>
          <p className="font-medium">No price history yet</p>
          <p className="text-sm text-muted-foreground">
            This product does not have enough imported retail prices for a
            chart.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="h-80 w-full">
        <ResponsiveContainer height="100%" width="100%">
          <LineChart
            data={chartData.rows}
            margin={{ bottom: 0, left: 0, right: 12, top: 12 }}
          >
            <CartesianGrid className="stroke-muted" strokeDasharray="3 3" />
            <XAxis
              axisLine={false}
              dataKey="observed_date"
              tickFormatter={formatShortDate}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              domain={priceDomain}
              tickFormatter={formatChartCurrency}
              tickLine={false}
              width={72}
            />
            <Tooltip content={<PriceHistoryTooltip />} />
            {chartData.series.map((series) => (
              <Line
                activeDot={{ r: 5 }}
                connectNulls
                dataKey={series.dataKey}
                dot={{ r: 3 }}
                key={series.id}
                name={series.name}
                stroke={series.color}
                strokeWidth={2}
                type="monotone"
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-3">
        {chartData.series.map((series) => (
          <div
            className="flex items-center gap-2 text-sm text-muted-foreground"
            key={series.id}
          >
            <span
              className="size-3 rounded-full"
              style={{ backgroundColor: series.color }}
            />
            {series.name}
          </div>
        ))}
      </div>
    </div>
  )
}

function PriceHistoryTooltip({
  active,
  label,
  payload,
}: PriceHistoryTooltipProps) {
  const visiblePayload = payload?.filter(
    (item) => item.value !== null && item.value !== undefined,
  )

  if (!active || !visiblePayload?.length) {
    return null
  }

  return (
    <div className="min-w-52 rounded-xl border bg-popover p-3 text-popover-foreground shadow-md">
      <p className="mb-2 text-sm font-medium">{label}</p>
      <div className="space-y-2">
        {visiblePayload.map((item) => {
          const dataKey = String(item.dataKey)
          const minPrice = getChartPriceValue(item.payload?.[`${dataKey}__min`])
          const maxPrice = getChartPriceValue(item.payload?.[`${dataKey}__max`])
          const isSpecialSale = item.payload?.[`${dataKey}__sale`] === true
          const range = formatPriceRangeValue(minPrice, maxPrice)

          return (
            <div className="space-y-1" key={dataKey}>
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="flex items-center gap-2">
                  <span
                    className="size-2.5 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  {item.name}
                  {isSpecialSale && (
                    <span className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                      Special sale
                    </span>
                  )}
                </span>
                <span className="font-medium">
                  {formatCurrencyValue(item.value)}
                </span>
              </div>
              {range && (
                <p className="pl-4 text-xs text-muted-foreground">
                  Range {range}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function buildPriceHistoryChartData(
  points: Array<RetailerDailyRetailPriceHistoryPoint>,
): PriceHistoryChartData {
  const retailers = new Map<string, string>()
  const rowsByDate = new Map<string, PriceHistoryDatum>()

  for (const point of points) {
    retailers.set(point.retailer.id, point.retailer.name)

    const dataKey = getRetailerPriceDataKey(point.retailer.id)
    const row = rowsByDate.get(point.observed_date) ?? {
      observed_date: point.observed_date,
    }

    row[dataKey] = parseNullableNumber(point.average_price_eur)
    row[`${dataKey}__min`] = parseNullableNumber(point.min_price_eur)
    row[`${dataKey}__max`] = parseNullableNumber(point.max_price_eur)
    row[`${dataKey}__sale`] = point.has_special_sale
    rowsByDate.set(point.observed_date, row)
  }

  const series = [...retailers.entries()]
    .sort(([, firstName], [, secondName]) =>
      firstName.localeCompare(secondName),
    )
    .map(([id, name], index) => {
      const dataKey = getRetailerPriceDataKey(id)

      return {
        color: CHART_COLORS[index % CHART_COLORS.length],
        dataKey,
        id,
        maxKey: `${dataKey}__max`,
        minKey: `${dataKey}__min`,
        name,
      }
    })

  return {
    rows: [...rowsByDate.values()].sort((first, second) =>
      first.observed_date.localeCompare(second.observed_date),
    ),
    series,
  }
}

function getChartPriceValue(value?: boolean | number | string | null) {
  return typeof value === "boolean" ? null : value
}

function getRetailerPriceDataKey(retailerId: string) {
  return `retailer_${retailerId.replace(/-/g, "_")}`
}

function getPriceHistoryDomain(
  rows: Array<PriceHistoryDatum>,
  series: Array<PriceHistorySeries>,
): [number, number] | ["auto", "auto"] {
  const values = rows.flatMap((row) =>
    series
      .map((item) => row[item.dataKey])
      .filter((value): value is number => typeof value === "number"),
  )

  if (values.length === 0) {
    return ["auto", "auto"]
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const spread = Math.max(max - min, 0.1)
  const padding = spread * 0.35

  return [Math.max(0, min - padding), max + padding]
}

type PriceObservationRowProps = {
  isBestPrice: boolean
  observation: RetailerPriceObservationSummary
  priceDelta?: string
}

function PriceObservationRow({
  isBestPrice,
  observation,
  priceDelta,
}: PriceObservationRowProps) {
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
    <div
      className={
        isBestPrice
          ? "rounded-2xl border border-primary/40 bg-primary/10 p-4"
          : "rounded-2xl border bg-background/60 p-4"
      }
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-semibold">{observation.retailer.name}</p>
            <Badge variant="secondary">{observation.store_count} stores</Badge>
            {isBestPrice && <Badge>Best price</Badge>}
            {observation.has_store_price_variance && (
              <Badge variant="outline">Price varies by store</Badge>
            )}
            {observation.has_special_sale && (
              <Badge variant="outline">Special sale</Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            <span>{observation.observed_date}</span>
            <span>Latest observation</span>
          </div>
        </div>

        <div className="shrink-0 text-left sm:text-right">
          <p className="text-2xl font-semibold tracking-tight">
            {retailPrice ? formatCurrency(retailPrice) : "No price"}
          </p>
          <p className="text-sm text-muted-foreground">
            {formatCurrency(observation.average_unit_price_eur)} avg per unit
          </p>
          {!isBestPrice && priceDelta && (
            <p className="text-sm font-medium text-muted-foreground">
              {priceDelta} vs best
            </p>
          )}
          <div className="mt-2 flex flex-col gap-1 text-xs text-muted-foreground">
            {retailPriceRange && <span>Price range {retailPriceRange}</span>}
            {unitPriceRange && <span>Unit range {unitPriceRange}</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

type CurrentPriceTileProps = {
  isPending: boolean
  latestObservationDate?: string
  observation?: RetailerPriceObservationSummary
  price?: string
  retailerName?: string
  retailersCount: number
}

function CurrentPriceTile({
  isPending,
  latestObservationDate,
  observation,
  price,
  retailerName,
  retailersCount,
}: CurrentPriceTileProps) {
  return (
    <div className="flex min-h-44 flex-col justify-between rounded-2xl border border-primary/30 bg-primary/10 p-5">
      <div>
        <Tags className="mb-3 size-5 text-primary" />
        <p className="text-sm text-muted-foreground">
          Current lowest price{retailerName ? ` at ${retailerName}` : ""}
        </p>
        <div className="mt-2 flex flex-wrap items-end gap-x-3 gap-y-1">
          <p className="text-4xl font-semibold tracking-tight sm:text-5xl">
            {isPending ? "Loading" : price || "Not available"}
          </p>
          {observation?.average_unit_price_eur && (
            <p className="pb-1 text-sm text-muted-foreground">
              {formatCurrency(observation.average_unit_price_eur)} per unit
            </p>
          )}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
        <Badge variant="secondary">
          {isPending ? "Loading retailers" : `${retailersCount} retailers`}
        </Badge>
        {observation?.store_count && (
          <Badge variant="secondary">{observation.store_count} stores</Badge>
        )}
        {latestObservationDate && (
          <Badge variant="outline">Updated {latestObservationDate}</Badge>
        )}
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
      <div className="flex h-72 items-center justify-center bg-muted/40 sm:h-80 lg:h-full lg:max-h-[28rem]">
        <img
          alt={name}
          className="h-full w-full object-contain p-6"
          loading="lazy"
          onError={() => setHasError(true)}
          src={imageUrl}
        />
      </div>
    )
  }

  return (
    <div className="flex h-72 items-center justify-center bg-gradient-to-br from-primary/20 via-primary/10 to-background sm:h-80 lg:h-full lg:max-h-[28rem]">
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
  description: string
  productsBackSearch: ProductsBackSearch
  title: string
}

function ProductMessage({
  description,
  productsBackSearch,
  title,
}: ProductMessageProps) {
  return (
    <div className="space-y-6 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/products" search={productsBackSearch}>
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

function useProductsBackSearch() {
  const [productsBackSearch, setProductsBackSearch] =
    useState<ProductsBackSearch>({})

  useEffect(() => {
    const productsPath = window.sessionStorage.getItem(
      LAST_PRODUCTS_PATH_STORAGE_KEY,
    )

    if (!productsPath) {
      return
    }

    const productsUrl = new URL(productsPath, window.location.origin)
    const page = Number(productsUrl.searchParams.get("page"))
    const q = productsUrl.searchParams.get("q") ?? undefined

    setProductsBackSearch({
      page: Number.isInteger(page) && page > 1 ? page : undefined,
      q,
    })
  }, [])

  return productsBackSearch
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
    .map((observation) => {
      const price = getMinPrice(observation)

      return price
        ? { observation, price, retailer: observation.retailer }
        : undefined
    })
    .filter((price): price is NonNullable<typeof price> => Boolean(price))
    .sort((first, second) => Number(first.price) - Number(second.price))[0]
}

function parseNullableNumber(value?: string | null) {
  if (!value) {
    return null
  }

  return Number(value)
}

function formatShortDate(value: string) {
  return new Intl.DateTimeFormat("hr-HR", {
    day: "2-digit",
    month: "2-digit",
  }).format(new Date(value))
}

function formatChartCurrency(value: number) {
  return `${value.toFixed(2)} €`
}

function formatCurrencyValue(value?: number | string | null) {
  if (value === null || value === undefined) {
    return "Not available"
  }

  return new Intl.NumberFormat("hr-HR", {
    currency: "EUR",
    style: "currency",
  }).format(Number(value))
}

function formatPriceRangeValue(
  minPrice?: number | string | null,
  maxPrice?: number | string | null,
) {
  if (
    minPrice === null ||
    minPrice === undefined ||
    maxPrice === null ||
    maxPrice === undefined ||
    Number(minPrice) === Number(maxPrice)
  ) {
    return undefined
  }

  return `${formatCurrencyValue(minPrice)} to ${formatCurrencyValue(maxPrice)}`
}

function formatCurrency(value: string) {
  return new Intl.NumberFormat("hr-HR", {
    currency: "EUR",
    style: "currency",
  }).format(Number(value))
}

function formatPackageSize(product: ProductPublic) {
  if (!product.net_quantity && !product.unit_of_measure) {
    return undefined
  }

  return [formatQuantity(product.net_quantity), product.unit_of_measure]
    .filter(Boolean)
    .join(" × ")
}

function formatQuantity(value?: string | null) {
  if (!value) {
    return undefined
  }

  return new Intl.NumberFormat("hr-HR", {
    maximumFractionDigits: 3,
  }).format(Number(value.replace(",", ".")))
}

function formatObservationsPriceSpread(
  observations: Array<RetailerPriceObservationSummary>,
) {
  const prices = observations
    .map(getAveragePrice)
    .filter((price): price is string => Boolean(price))
    .sort((first, second) => Number(first) - Number(second))

  const minPrice = prices[0]
  const maxPrice = prices[prices.length - 1]

  if (!minPrice || !maxPrice) {
    return undefined
  }

  if (minPrice === maxPrice) {
    return formatCurrency(minPrice)
  }

  return `${formatCurrency(minPrice)} to ${formatCurrency(maxPrice)}`
}

function formatPriceDeltaFromBest(
  price?: string | null,
  bestPrice?: string | null,
) {
  if (!price || !bestPrice) {
    return undefined
  }

  const delta = Number(price) - Number(bestPrice)

  if (delta <= 0) {
    return undefined
  }

  return `+${formatCurrency(delta.toString())}`
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
  return observation.average_price_eur
}

function getMinPrice(observation: RetailerPriceObservationSummary) {
  return observation.min_price_eur
}

function getMaxPrice(observation: RetailerPriceObservationSummary) {
  return observation.max_price_eur
}

function formatPriceRange(minPrice?: string | null, maxPrice?: string | null) {
  if (!minPrice || !maxPrice || minPrice === maxPrice) {
    return undefined
  }

  return `${formatCurrency(minPrice)} to ${formatCurrency(maxPrice)}`
}

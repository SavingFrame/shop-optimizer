import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Barcode,
  CalendarDays,
  ImageIcon,
  ListPlus,
  PackageSearch,
  Search,
  Trash2,
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
  type ProductListItemDetailPublic,
  type ProductListRetailerPriceHistoryPoint,
  ProductListsService,
  type ProductPublic,
  ProductsService,
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/product-lists/$productListId")({
  component: ProductListDetailPage,
  head: () => ({
    meta: [
      {
        title: "Product list - Shop Optimizer",
      },
    ],
  }),
})

function ProductListDetailPage() {
  const { productListId } = Route.useParams()
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedSearch(search.trim())
    }, 300)

    return () => window.clearTimeout(timeoutId)
  }, [search])

  const productListQuery = useQuery({
    queryKey: ["product-lists", productListId],
    queryFn: () => ProductListsService.readProductList({ productListId }),
  })

  const itemsQuery = useQuery({
    queryKey: ["product-lists", productListId, "items"],
    queryFn: () => ProductListsService.readProductListItems({ productListId }),
  })

  const priceHistoryQuery = useQuery({
    queryKey: [
      "product-lists",
      productListId,
      "price-history",
      "retail",
      "chart",
    ],
    queryFn: () =>
      ProductListsService.productListRetailPriceHistoryChart({ productListId }),
  })

  const productsQuery = useQuery({
    enabled: debouncedSearch.length > 0,
    placeholderData: keepPreviousData,
    queryKey: ["products", "product-list-picker", debouncedSearch],
    queryFn: () =>
      ProductsService.readProducts({
        limit: 8,
        q: debouncedSearch,
      }),
  })

  const productList = productListQuery.data
  const items = itemsQuery.data ?? []
  const products = productsQuery.data?.data ?? []
  const existingProductIds = new Set(items.map((item) => item.product_id))

  if (productListQuery.isPending) {
    return (
      <div className="space-y-6 pb-12">
        <div className="h-10 w-36 animate-pulse rounded-full bg-card" />
        <div className="h-64 animate-pulse rounded-3xl border bg-card/70" />
      </div>
    )
  }

  if (productListQuery.isError || !productList) {
    return (
      <ProductListMessage
        title="Could not load product list"
        description="Check that the list exists and that you are logged in."
      />
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/product-lists">
          <ArrowLeft className="size-4" />
          Back to product lists
        </Link>
      </Button>

      <section className="grid gap-6 lg:grid-cols-[1fr_0.75fr] lg:items-stretch">
        <div className="space-y-4">
          <Badge variant="secondary" className="gap-2 px-3 py-1">
            <ListPlus className="size-3.5 text-primary" />
            Product list
          </Badge>
          <div className="space-y-3">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              {productList.name}
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground">
              {productList.description ||
                "Add canonical products and quantities to this reusable basket."}
            </p>
          </div>
        </div>

        <Card className="bg-card/80">
          <CardHeader>
            <CardTitle>List summary</CardTitle>
            <CardDescription>
              Basket comparison and price history will use these products.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <SummaryTile label="Items" value={items.length.toString()} />
            <SummaryTile
              label="Products"
              value={new Set(
                items.map((item) => item.product_id),
              ).size.toString()}
            />
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Basket price history</CardTitle>
          <CardDescription>
            Estimated total price for this list over time, grouped by retailer.
            Missing products are marked in the tooltip.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BasketPriceHistoryChart
            isError={priceHistoryQuery.isError}
            isPending={priceHistoryQuery.isPending}
            points={priceHistoryQuery.data ?? []}
          />
        </CardContent>
      </Card>

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Add products</CardTitle>
            <CardDescription>
              Search the product catalog and add canonical products to this
              list.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="h-11 rounded-2xl pl-10"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search products to add..."
                value={search}
              />
            </div>

            {debouncedSearch.length === 0 && (
              <div className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-2xl border bg-background/60 p-6 text-center">
                <PackageSearch className="size-10 text-muted-foreground" />
                <div>
                  <p className="font-medium">Search for a product</p>
                  <p className="text-sm text-muted-foreground">
                    Add products by name, brand, category, or barcode.
                  </p>
                </div>
              </div>
            )}

            {productsQuery.isPending && debouncedSearch.length > 0 && (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, index) => (
                  <div
                    className="h-20 animate-pulse rounded-2xl border bg-background/60"
                    key={index}
                  />
                ))}
              </div>
            )}

            {productsQuery.isError && (
              <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
                Could not search products.
              </div>
            )}

            {!productsQuery.isPending &&
              debouncedSearch.length > 0 &&
              products.length === 0 && (
                <div className="rounded-2xl border bg-background/60 p-4 text-sm text-muted-foreground">
                  No matching products found.
                </div>
              )}

            {!productsQuery.isPending && products.length > 0 && (
              <div className="space-y-3">
                {products.map((product) => (
                  <ProductSearchRow
                    isAlreadyAdded={existingProductIds.has(product.id)}
                    key={product.id}
                    product={product}
                    productListId={productList.id}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Products in this list</CardTitle>
            <CardDescription>
              Adjust quantities or remove products from the basket.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {itemsQuery.isPending && (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div
                    className="h-24 animate-pulse rounded-2xl border bg-background/60"
                    key={index}
                  />
                ))}
              </div>
            )}

            {itemsQuery.isError && (
              <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
                Could not load list items.
              </div>
            )}

            {!itemsQuery.isPending &&
              !itemsQuery.isError &&
              items.length === 0 && (
                <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border bg-background/60 p-6 text-center">
                  <ListPlus className="size-10 text-muted-foreground" />
                  <div>
                    <p className="font-medium">No products yet</p>
                    <p className="text-sm text-muted-foreground">
                      Search on the left to add your first product.
                    </p>
                  </div>
                </div>
              )}

            {!itemsQuery.isPending && items.length > 0 && (
              <div className="space-y-3">
                {items.map((item) => (
                  <ProductListItemRow key={item.id} item={item} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

type BasketPriceHistoryChartProps = {
  isError: boolean
  isPending: boolean
  points: Array<ProductListRetailerPriceHistoryPoint>
}

type BasketPriceHistoryChartData = {
  rows: Array<BasketPriceHistoryDatum>
  series: Array<BasketPriceHistorySeries>
}

type BasketPriceHistoryDatum = {
  observed_date: string
} & Record<string, boolean | number | string | null>

type BasketPriceHistorySeries = {
  color: string
  dataKey: string
  id: string
  name: string
}

type BasketPriceHistoryTooltipPayload = {
  color?: string
  dataKey?: string | number
  name?: string
  payload?: BasketPriceHistoryDatum
  value?: number | string | null
}

type BasketPriceHistoryTooltipProps = {
  active?: boolean
  label?: string
  payload?: Array<BasketPriceHistoryTooltipPayload>
}

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
]

function BasketPriceHistoryChart({
  isError,
  isPending,
  points,
}: BasketPriceHistoryChartProps) {
  const chartData = useMemo(() => buildBasketPriceHistoryData(points), [points])

  if (isPending) {
    return <div className="h-80 animate-pulse rounded-2xl bg-background/60" />
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
        Could not load basket price history.
      </div>
    )
  }

  if (chartData.rows.length === 0 || chartData.series.length === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center gap-3 rounded-2xl border bg-background/60 p-6 text-center">
        <CalendarDays className="size-10 text-muted-foreground" />
        <div>
          <p className="font-medium">No basket history yet</p>
          <p className="text-sm text-muted-foreground">
            Add products with imported price observations to see this list over
            time.
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
              tickFormatter={formatChartCurrency}
              tickLine={false}
              width={72}
            />
            <Tooltip content={<BasketPriceHistoryTooltip />} />
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

function BasketPriceHistoryTooltip({
  active,
  label,
  payload,
}: BasketPriceHistoryTooltipProps) {
  const visiblePayload = payload?.filter(
    (item) => item.value !== null && item.value !== undefined,
  )

  if (!active || !visiblePayload?.length) {
    return null
  }

  return (
    <div className="min-w-60 rounded-xl border bg-popover p-3 text-popover-foreground shadow-md">
      <p className="mb-2 text-sm font-medium">{label}</p>
      <div className="space-y-2">
        {visiblePayload.map((item) => {
          const dataKey = String(item.dataKey)
          const matchedItemCount = item.payload?.[`${dataKey}__matched`]
          const totalItemCount = item.payload?.[`${dataKey}__total`]
          const hasMissingPrices =
            item.payload?.[`${dataKey}__missing`] === true
          const hasSpecialSale = item.payload?.[`${dataKey}__sale`] === true

          return (
            <div className="space-y-1" key={dataKey}>
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="flex items-center gap-2">
                  <span
                    className="size-2.5 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  {item.name}
                </span>
                <span className="font-medium">
                  {formatCurrencyValue(item.value)}
                </span>
              </div>
              <div className="flex flex-wrap gap-2 pl-4 text-xs text-muted-foreground">
                <span>
                  {matchedItemCount}/{totalItemCount} products priced
                </span>
                {hasMissingPrices && <span>Missing prices</span>}
                {hasSpecialSale && <span>Special sale included</span>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function buildBasketPriceHistoryData(
  points: Array<ProductListRetailerPriceHistoryPoint>,
): BasketPriceHistoryChartData {
  const retailers = new Map<string, string>()
  const rowsByDate = new Map<string, BasketPriceHistoryDatum>()

  for (const point of points) {
    retailers.set(point.retailer.id, point.retailer.name)

    const dataKey = getRetailerPriceDataKey(point.retailer.id)
    const row = rowsByDate.get(point.observed_date) ?? {
      observed_date: point.observed_date,
    }

    row[dataKey] = parseNullableNumber(point.total_price_eur)
    row[`${dataKey}__matched`] = point.matched_item_count
    row[`${dataKey}__total`] = point.total_item_count
    row[`${dataKey}__missing`] = point.has_missing_prices
    row[`${dataKey}__sale`] = point.has_special_sale
    rowsByDate.set(point.observed_date, row)
  }

  const series = [...retailers.entries()]
    .sort(([, firstName], [, secondName]) =>
      firstName.localeCompare(secondName),
    )
    .map(([id, name], index) => ({
      color: CHART_COLORS[index % CHART_COLORS.length],
      dataKey: getRetailerPriceDataKey(id),
      id,
      name,
    }))

  return {
    rows: [...rowsByDate.values()].sort((first, second) =>
      first.observed_date.localeCompare(second.observed_date),
    ),
    series,
  }
}

function getRetailerPriceDataKey(retailerId: string) {
  return `retailer_${retailerId.replace(/-/g, "_")}`
}

type ProductSearchRowProps = {
  isAlreadyAdded: boolean
  product: ProductPublic
  productListId: string
}

function ProductSearchRow({
  isAlreadyAdded,
  product,
  productListId,
}: ProductSearchRowProps) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const addMutation = useMutation({
    mutationFn: () =>
      ProductListsService.createProductListItem({
        productListId,
        requestBody: {
          product_id: product.id,
          quantity: "1",
        },
      }),
    onError: () => {
      showErrorToast("Could not add product to list.")
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["product-lists", productListId, "items"],
      })
      showSuccessToast("Product added to list.")
    },
  })

  return (
    <div className="grid gap-3 rounded-2xl border bg-background/60 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
      <ProductSummary product={product} />
      <LoadingButton
        disabled={isAlreadyAdded}
        loading={addMutation.isPending}
        onClick={() => addMutation.mutate()}
        size="sm"
      >
        <ListPlus className="size-4" />
        {isAlreadyAdded ? "Added" : "Add"}
      </LoadingButton>
    </div>
  )
}

type ProductListItemRowProps = {
  item: ProductListItemDetailPublic
}

function ProductListItemRow({ item }: ProductListItemRowProps) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [quantity, setQuantity] = useState(
    formatQuantityForInput(item.quantity),
  )

  const updateMutation = useMutation({
    mutationFn: () =>
      ProductListsService.updateProductListItem({
        itemId: item.id,
        productListId: item.product_list_id,
        requestBody: {
          quantity,
        },
      }),
    onError: () => {
      showErrorToast("Could not update quantity.")
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["product-lists", item.product_list_id, "items"],
      })
      showSuccessToast("Quantity updated.")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () =>
      ProductListsService.deleteProductListItem({
        itemId: item.id,
        productListId: item.product_list_id,
      }),
    onError: () => {
      showErrorToast("Could not remove product.")
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["product-lists", item.product_list_id, "items"],
      })
      showSuccessToast("Product removed from list.")
    },
  })

  return (
    <div className="space-y-4 rounded-2xl border bg-background/60 p-4">
      <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-start">
        <ProductSummary product={item.product} />
        <Button
          aria-label={`Remove ${item.product.name}`}
          disabled={deleteMutation.isPending}
          onClick={() => deleteMutation.mutate()}
          size="icon"
          variant="ghost"
        >
          <Trash2 className="size-4" />
        </Button>
      </div>
      <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
        <div className="space-y-2">
          <Label htmlFor={`quantity-${item.id}`}>Quantity</Label>
          <Input
            id={`quantity-${item.id}`}
            min="0"
            onChange={(event) => setQuantity(event.target.value)}
            step="1"
            type="number"
            value={quantity}
          />
        </div>
        <LoadingButton
          disabled={quantity === item.quantity || Number(quantity) <= 0}
          loading={updateMutation.isPending}
          onClick={() => updateMutation.mutate()}
        >
          Save
        </LoadingButton>
      </div>
    </div>
  )
}

type ProductSummaryProps = {
  product: ProductPublic
}

function ProductSummary({ product }: ProductSummaryProps) {
  return (
    <div className="flex min-w-0 gap-3">
      <div className="flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl border bg-muted/40">
        {product.image_url ? (
          <img
            alt={product.name}
            className="h-full w-full object-contain p-2"
            loading="lazy"
            src={product.image_url}
          />
        ) : (
          <ImageIcon className="size-6 text-muted-foreground" />
        )}
      </div>
      <div className="min-w-0 space-y-1">
        <Link
          className="line-clamp-2 font-medium hover:text-primary"
          params={{ productId: product.id }}
          to="/products/$productId"
        >
          {product.name}
        </Link>
        <div className="flex flex-wrap gap-2">
          {product.category && (
            <Badge variant="secondary">{product.category}</Badge>
          )}
          {product.brand && <Badge variant="outline">{product.brand}</Badge>}
        </div>
        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
          {product.net_quantity && <span>{product.net_quantity}</span>}
          {product.unit_of_measure && <span>{product.unit_of_measure}</span>}
          {product.barcode && (
            <span className="inline-flex items-center gap-1">
              <Barcode className="size-3" />
              {product.barcode}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

type SummaryTileProps = {
  label: string
  value: string
}

function formatQuantityForInput(quantity?: string) {
  if (!quantity) {
    return "1"
  }

  return quantity.replace(/(\.\d*?[1-9])0+$|\.0+$/, "$1")
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

function SummaryTile({ label, value }: SummaryTileProps) {
  return (
    <div className="rounded-2xl border bg-background/60 p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
    </div>
  )
}

type ProductListMessageProps = {
  description: string
  title: string
}

function ProductListMessage({ description, title }: ProductListMessageProps) {
  return (
    <div className="space-y-6 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/product-lists">
          <ArrowLeft className="size-4" />
          Back to product lists
        </Link>
      </Button>
      <Card className="border-destructive/30 bg-destructive/5">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
      </Card>
    </div>
  )
}

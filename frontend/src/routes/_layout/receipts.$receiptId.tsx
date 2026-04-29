import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  CheckCircle2,
  CircleSlash,
  ReceiptText,
  Search,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import {
  type ProductPublic,
  ProductsService,
  type Receipt,
  type ReceiptItemReviewPublic,
  ReceiptsService,
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
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/receipts/$receiptId")({
  component: ReceiptDetailPage,
  head: () => ({
    meta: [
      {
        title: "Receipt review - Shop Optimizer",
      },
    ],
  }),
})

function ReceiptDetailPage() {
  const { receiptId } = Route.useParams()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const receiptQuery = useQuery({
    queryKey: ["receipts", receiptId],
    queryFn: () => ReceiptsService.readReceipt({ receiptId }),
  })

  const itemsQuery = useQuery({
    queryKey: ["receipts", receiptId, "items"],
    queryFn: () => ReceiptsService.readReceiptItems({ receiptId }),
  })

  const completeMutation = useMutation({
    mutationFn: () =>
      ReceiptsService.updateReceipt({
        receiptId,
        requestBody: { status: "completed" },
      }),
    onError: () => {
      showErrorToast("All receipt lines must be matched or skipped first.")
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["receipts"] }),
        queryClient.invalidateQueries({ queryKey: ["receipts", receiptId] }),
      ])
      showSuccessToast("Receipt completed.")
    },
  })

  const receipt = receiptQuery.data
  const items = itemsQuery.data ?? []
  const stats = useMemo(() => getReceiptStats(items), [items])
  const canComplete = stats.total > 0 && stats.open === 0
  const isCompleted = receipt?.status === "completed"

  if (receiptQuery.isPending) {
    return (
      <div className="space-y-6 pb-12">
        <div className="h-10 w-40 animate-pulse rounded-full bg-card" />
        <div className="h-96 animate-pulse rounded-3xl border bg-card/70" />
      </div>
    )
  }

  if (receiptQuery.isError || !receipt) {
    return (
      <ReceiptMessage
        description="Check that the receipt exists and belongs to your account."
        title="Could not load receipt"
      />
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/receipts">
          <ArrowLeft className="size-4" />
          Back to receipts
        </Link>
      </Button>

      <section className="grid gap-6 lg:grid-cols-[1fr_0.75fr]">
        <Card className="bg-card/80">
          <CardHeader className="gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="gap-2 px-3 py-1">
                <ReceiptText className="size-3.5 text-primary" />
                Receipt review
              </Badge>
              <Badge variant={isCompleted ? "default" : "secondary"}>
                {receipt.status ?? "draft"}
              </Badge>
            </div>
            <div className="space-y-3">
              <CardTitle className="text-3xl sm:text-5xl">
                SPAR receipt
              </CardTitle>
              <CardDescription className="text-base leading-7">
                Keep suggested products, choose better matches, or skip lines
                like bags and non-product receipt entries.
              </CardDescription>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Review progress</CardTitle>
            <CardDescription>
              Complete when every line is matched or skipped.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <InfoTile label="Total" value={stats.total.toString()} />
              <InfoTile label="Matched" value={stats.matched.toString()} />
              <InfoTile label="Open" value={stats.open.toString()} />
            </div>
            <div className="rounded-2xl border bg-background/60 p-4 text-sm">
              <p className="text-muted-foreground">Receipt total</p>
              <p className="mt-1 text-2xl font-semibold">
                {formatCurrency(receipt.total_eur)}
              </p>
              <p className="mt-1 text-muted-foreground">
                {formatDateTime(receipt.purchase_datetime)}
              </p>
            </div>
            <LoadingButton
              className="w-full"
              disabled={!canComplete || isCompleted}
              loading={completeMutation.isPending}
              onClick={() => completeMutation.mutate()}
            >
              <CheckCircle2 className="size-4" />
              {isCompleted ? "Completed" : "Complete receipt"}
            </LoadingButton>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Receipt items</CardTitle>
          <CardDescription>
            Product search uses the existing catalog endpoint.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {itemsQuery.isPending && (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <div
                  className="h-20 animate-pulse rounded-2xl border bg-background/60"
                  key={index}
                />
              ))}
            </div>
          )}

          {itemsQuery.isError && (
            <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-muted-foreground">
              Could not load receipt items.
            </div>
          )}

          {!itemsQuery.isPending &&
            !itemsQuery.isError &&
            items.length === 0 && (
              <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border bg-background/60 p-6 text-center">
                <ReceiptText className="size-10 text-muted-foreground" />
                <div>
                  <p className="font-medium">No receipt items</p>
                  <p className="text-sm text-muted-foreground">
                    This receipt does not have parsed lines yet.
                  </p>
                </div>
              </div>
            )}

          {!itemsQuery.isPending && items.length > 0 && (
            <ReceiptItemsTable
              disabled={isCompleted}
              items={items}
              receipt={receipt}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

type ReceiptItemsTableProps = {
  disabled: boolean
  items: Array<ReceiptItemReviewPublic>
  receipt: Receipt
}

function ReceiptItemsTable({
  disabled,
  items,
  receipt,
}: ReceiptItemsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-16">Line</TableHead>
          <TableHead>Receipt line</TableHead>
          <TableHead className="w-28">Qty</TableHead>
          <TableHead className="w-32">Total</TableHead>
          <TableHead className="min-w-80">Product</TableHead>
          <TableHead className="w-28">Skip</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <ReceiptItemRow
            disabled={disabled}
            item={item}
            key={item.id}
            receiptId={receipt.id ?? item.receipt_id}
          />
        ))}
      </TableBody>
    </Table>
  )
}

type ReceiptItemRowProps = {
  disabled: boolean
  item: ReceiptItemReviewPublic
  receiptId: string
}

function ReceiptItemRow({ disabled, item, receiptId }: ReceiptItemRowProps) {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const updateMutation = useMutation({
    mutationFn: (requestBody: {
      product_id?: string | null
      is_skipped?: boolean
    }) =>
      ReceiptsService.updateReceiptItem({
        itemId: item.id,
        receiptId,
        requestBody,
      }),
    onError: () => {
      showErrorToast("Could not update receipt item.")
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["receipts", receiptId, "items"],
      })
    },
  })

  const isSkipped = item.is_skipped === true
  const isSaving = updateMutation.isPending

  return (
    <TableRow className={isSkipped ? "opacity-60" : undefined}>
      <TableCell className="font-medium">#{item.line_number}</TableCell>
      <TableCell>
        <div className="min-w-64 space-y-1 whitespace-normal">
          <p className="font-medium">{item.raw_name}</p>
          <p className="text-xs text-muted-foreground">
            Unit price {formatOptionalCurrency(item.unit_price_eur)}
          </p>
        </div>
      </TableCell>
      <TableCell>
        {item.quantity}
        {item.unit_of_measure ? ` ${item.unit_of_measure}` : ""}
      </TableCell>
      <TableCell>{formatCurrency(item.line_total_eur)}</TableCell>
      <TableCell>
        <ProductSelector
          disabled={disabled || isSkipped || isSaving}
          item={item}
          onChange={(productId) =>
            updateMutation.mutate({ product_id: productId, is_skipped: false })
          }
        />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Checkbox
            checked={isSkipped}
            disabled={disabled || isSaving}
            onCheckedChange={(checked) =>
              updateMutation.mutate({ is_skipped: checked === true })
            }
          />
          <span className="text-sm text-muted-foreground">Skip</span>
        </div>
      </TableCell>
    </TableRow>
  )
}

type ProductSelectorProps = {
  disabled: boolean
  item: ReceiptItemReviewPublic
  onChange: (productId: string | null) => void
}

function ProductSelector({ disabled, item, onChange }: ProductSelectorProps) {
  const [search, setSearch] = useState(item.product?.name ?? item.raw_name)
  const normalizedSearch = search.trim()

  useEffect(() => {
    if (item.product) {
      setSearch(item.product.name)
    }
  }, [item.product])

  const productsQuery = useQuery({
    enabled: normalizedSearch.length >= 2 && !disabled,
    queryKey: ["products", "receipt-search", normalizedSearch],
    queryFn: () =>
      ProductsService.readProducts({
        limit: 10,
        q: normalizedSearch,
      }),
  })

  const options = useMemo(
    () => buildProductOptions(item.product, productsQuery.data?.data ?? []),
    [item.product, productsQuery.data?.data],
  )

  return (
    <div className="min-w-80 space-y-2">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          disabled={disabled}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search product..."
          value={search}
        />
      </div>
      <Select
        disabled={disabled || productsQuery.isPending}
        onValueChange={(value) => onChange(value === "none" ? null : value)}
        value={item.product_id ?? "none"}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Choose product" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="none">No product selected</SelectItem>
          {options.map((product) => (
            <SelectItem key={product.id} value={product.id}>
              {formatProductOption(product)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {item.product && (
        <p className="text-xs text-muted-foreground">
          Selected: {item.product.name}
        </p>
      )}
    </div>
  )
}

function buildProductOptions(
  selectedProduct: ProductPublic | null | undefined,
  products: Array<ProductPublic>,
) {
  const options = new Map<string, ProductPublic>()

  if (selectedProduct) {
    options.set(selectedProduct.id, selectedProduct)
  }

  for (const product of products) {
    options.set(product.id, product)
  }

  return [...options.values()]
}

function formatProductOption(product: ProductPublic) {
  const parts = [product.name, product.brand, product.net_quantity].filter(
    Boolean,
  )
  return parts.join(" • ")
}

type ReceiptStats = {
  matched: number
  open: number
  skipped: number
  total: number
}

function getReceiptStats(items: Array<ReceiptItemReviewPublic>): ReceiptStats {
  const skipped = items.filter((item) => item.is_skipped).length
  const matched = items.filter(
    (item) => item.product_id && !item.is_skipped,
  ).length
  return {
    matched,
    open: items.length - matched - skipped,
    skipped,
    total: items.length,
  }
}

type InfoTileProps = {
  label: string
  value: string
}

function InfoTile({ label, value }: InfoTileProps) {
  return (
    <div className="rounded-2xl border bg-background/60 p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  )
}

type ReceiptMessageProps = {
  description: string
  title: string
}

function ReceiptMessage({ description, title }: ReceiptMessageProps) {
  return (
    <div className="space-y-6 pb-12">
      <Button variant="ghost" asChild>
        <Link to="/receipts">
          <ArrowLeft className="size-4" />
          Back to receipts
        </Link>
      </Button>
      <Card>
        <CardContent className="flex min-h-64 flex-col items-center justify-center gap-3 text-center">
          <CircleSlash className="size-10 text-muted-foreground" />
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

function formatDateTime(value?: string | null) {
  if (!value) {
    return "Unknown date"
  }

  return new Intl.DateTimeFormat("hr-HR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

function formatCurrency(value?: string | null) {
  if (!value) {
    return "Not available"
  }

  return new Intl.NumberFormat("hr-HR", {
    currency: "EUR",
    style: "currency",
  }).format(Number(value))
}

function formatOptionalCurrency(value?: string | null) {
  return value ? formatCurrency(value) : "Not available"
}

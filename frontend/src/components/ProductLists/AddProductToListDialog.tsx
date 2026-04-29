import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ListPlus, Plus } from "lucide-react"
import { useMemo, useState } from "react"

import { type ProductListPublic, ProductListsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"

type AddProductToListDialogProps = {
  productId: string
  productName: string
  trigger?: React.ReactNode
}

export function AddProductToListDialog({
  productId,
  productName,
  trigger,
}: AddProductToListDialogProps) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [open, setOpen] = useState(false)
  const [selectedListId, setSelectedListId] = useState("")
  const [newListName, setNewListName] = useState("")
  const [quantity, setQuantity] = useState("1")

  const listsQuery = useQuery({
    enabled: open,
    queryKey: ["product-lists"],
    queryFn: () => ProductListsService.readProductLists({ limit: 100 }),
  })

  const productLists = listsQuery.data?.data ?? []
  const trimmedNewListName = newListName.trim()
  const canSubmit =
    (selectedListId || trimmedNewListName) && Number(quantity) > 0

  const selectedList = useMemo(
    () => productLists.find((list) => list.id === selectedListId),
    [productLists, selectedListId],
  )

  const addMutation = useMutation({
    mutationFn: async () => {
      let targetList: ProductListPublic | undefined = selectedList

      if (!targetList) {
        targetList = await ProductListsService.createProductList({
          requestBody: {
            name: trimmedNewListName,
          },
        })
      }

      return ProductListsService.createProductListItem({
        productListId: targetList.id,
        requestBody: {
          product_id: productId,
          quantity,
        },
      })
    },
    onError: () => {
      showErrorToast("Could not add product to list.")
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["product-lists"] })
      showSuccessToast("Product added to list.")
      setOpen(false)
      setSelectedListId("")
      setNewListName("")
      setQuantity("1")
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button>
            <ListPlus className="size-4" />
            Add to list
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add product to list</DialogTitle>
          <DialogDescription>
            Save {productName} to an existing product list or create a new one.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {listsQuery.isError && (
            <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-3 text-sm text-muted-foreground">
              Could not load product lists.
            </div>
          )}

          {productLists.length > 0 && (
            <div className="space-y-2">
              <Label>Existing list</Label>
              <Select
                onValueChange={(value) => {
                  setSelectedListId(value)
                  setNewListName("")
                }}
                value={selectedListId}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a list" />
                </SelectTrigger>
                <SelectContent>
                  {productLists.map((list) => (
                    <SelectItem key={list.id} value={list.id}>
                      {list.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="new-product-list-name">New list name</Label>
            <Input
              id="new-product-list-name"
              onChange={(event) => {
                setNewListName(event.target.value)
                setSelectedListId("")
              }}
              placeholder="Weekly groceries"
              value={newListName}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="product-list-quantity">Quantity</Label>
            <Input
              id="product-list-quantity"
              min="0"
              onChange={(event) => setQuantity(event.target.value)}
              step="1"
              type="number"
              value={quantity}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" asChild>
            <Link to="/product-lists">Open lists</Link>
          </Button>
          <LoadingButton
            disabled={!canSubmit}
            loading={addMutation.isPending || listsQuery.isPending}
            onClick={() => addMutation.mutate()}
          >
            <Plus className="size-4" />
            Add product
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

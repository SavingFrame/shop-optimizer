import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/products")({
  component: ProductsLayout,
})

function ProductsLayout() {
  return <Outlet />
}

import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  beforeLoad: () => {
    throw redirect({ to: "/" })
  },
})

function Admin() {
  return null
}

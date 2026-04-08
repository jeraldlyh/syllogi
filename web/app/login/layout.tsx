import { api } from "@/lib/api";

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const respone = await api({
    method: "GET",
    service: "settings",
  });

  return <>{children}</>;
}

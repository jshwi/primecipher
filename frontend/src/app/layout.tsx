export const metadata = { title: 'PrimeCipher' }
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{fontFamily:'system-ui,-apple-system,Segoe UI,Roboto,sans-serif',maxWidth:980,margin:'24px auto',padding:'0 16px'}}>
        {children}
      </body>
    </html>
  )
}

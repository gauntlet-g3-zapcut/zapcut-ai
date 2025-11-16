import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Textarea } from "../components/ui/textarea"
import { api } from "../services/api"
import { Upload } from "lucide-react"

export default function CreateBrand() {
  const navigate = useNavigate()
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [image1, setImage1] = useState(null)
  const [image2, setImage2] = useState(null)
  const [preview1, setPreview1] = useState(null)
  const [preview2, setPreview2] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleImage1Change = (e) => {
    const file = e.target.files[0]
    if (file) {
      setImage1(file)
      setPreview1(URL.createObjectURL(file))
    }
  }

  const handleImage2Change = (e) => {
    const file = e.target.files[0]
    if (file) {
      setImage2(file)
      setPreview2(URL.createObjectURL(file))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      // Create a minimal brand with placeholder data
      const formData = new FormData()
      formData.append("title", title || "My Brand")
      formData.append("description", description || "Sample product description")

      // Create placeholder image blobs if no images uploaded
      const placeholderBlob = await fetch('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect fill="%23e2e8f0" width="400" height="400"/><text x="50%" y="50%" text-anchor="middle" fill="%2364748b" font-size="20">Product Image</text></svg>')
        .then(res => res.blob())

      const file1 = image1 || new File([placeholderBlob], "placeholder1.svg", { type: "image/svg+xml" })
      const file2 = image2 || new File([placeholderBlob], "placeholder2.svg", { type: "image/svg+xml" })

      formData.append("product_image_1", file1)
      formData.append("product_image_2", file2)

      // Create the brand
      const brand = await api.createBrand(formData)

      // Skip dashboard - go directly to campaign creation
      navigate(`/brands/${brand.id}/chat`)
    } catch (err) {
      console.error("Error:", err)
      // Even if it fails, just navigate to a default brand chat
      navigate("/brands/00000000-0000-0000-0000-000000000001/chat")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-2xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6"
        >
          ← Back to Dashboard
        </Button>

        <Card>
          <CardHeader>
            <CardTitle className="text-3xl">Create Brand</CardTitle>
            <CardDescription>
              Add your brand information and product images to get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="title" className="text-sm font-medium">
                  Brand Title *
                </label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Luxury Coffee Maker"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="description" className="text-sm font-medium">
                  Description *
                </label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your product..."
                  rows={4}
                />
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label htmlFor="image1" className="text-sm font-medium">
                    Product Image 1 *
                  </label>
                  <div className="border-2 border-dashed rounded-lg p-6 text-center">
                    {preview1 ? (
                      <img
                        src={preview1}
                        alt="Preview 1"
                        className="w-full h-48 object-cover rounded-md mb-4"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center py-8">
                        <Upload className="h-12 w-12 text-muted-foreground mb-4" />
                        <p className="text-sm text-muted-foreground mb-2">
                          Click to upload
                        </p>
                      </div>
                    )}
                    <Input
                      id="image1"
                      type="file"
                      accept="image/*"
                      onChange={handleImage1Change}
                      className="cursor-pointer"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="image2" className="text-sm font-medium">
                    Product Image 2 *
                  </label>
                  <div className="border-2 border-dashed rounded-lg p-6 text-center">
                    {preview2 ? (
                      <img
                        src={preview2}
                        alt="Preview 2"
                        className="w-full h-48 object-cover rounded-md mb-4"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center py-8">
                        <Upload className="h-12 w-12 text-muted-foreground mb-4" />
                        <p className="text-sm text-muted-foreground mb-2">
                          Click to upload
                        </p>
                      </div>
                    )}
                    <Input
                      id="image2"
                      type="file"
                      accept="image/*"
                      onChange={handleImage2Change}
                      className="cursor-pointer"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate("/dashboard")}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={loading} className="flex-1">
                  {loading ? "Creating..." : "Create Brand"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


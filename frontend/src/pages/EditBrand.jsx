import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Textarea } from "../components/ui/textarea"
import { api } from "../services/api"
import { Upload } from "lucide-react"

export default function EditBrand() {
  const navigate = useNavigate()
  const { brandId } = useParams()
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [image1, setImage1] = useState(null)
  const [image2, setImage2] = useState(null)
  const [preview1, setPreview1] = useState(null)
  const [preview2, setPreview2] = useState(null)
  const [existingImage1, setExistingImage1] = useState(null)
  const [existingImage2, setExistingImage2] = useState(null)
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchBrand = async () => {
      try {
        setFetching(true)
        const brand = await api.getBrand(brandId)
        setTitle(brand.title || "")
        setDescription(brand.description || "")
        setExistingImage1(brand.product_image_1_url)
        setExistingImage2(brand.product_image_2_url)
        setPreview1(brand.product_image_1_url)
        setPreview2(brand.product_image_2_url)
      } catch (err) {
        setError(err.message || "Failed to load brand")
      } finally {
        setFetching(false)
      }
    }

    if (brandId) {
      fetchBrand()
    }
  }, [brandId])

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
    
    if (!title || !description) {
      setError("Please fill in title and description")
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append("title", title)
      formData.append("description", description)
      
      // Only append images if new ones are uploaded
      if (image1) {
        formData.append("product_image_1", image1)
      }
      if (image2) {
        formData.append("product_image_2", image2)
      }

      await api.updateBrand(brandId, formData)
      // Navigate back to dashboard to show the updated brand
      navigate("/dashboard")
    } catch (err) {
      // Extract error message from error object
      let errorMessage = "Failed to update brand"
      if (err.message) {
        errorMessage = err.message
      } else if (err.detail) {
        errorMessage = err.detail
      } else if (typeof err === "string") {
        errorMessage = err
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      }
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (fetching) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center">
        <div className="text-muted-foreground">Loading brand...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-8">
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
            <CardTitle className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
              Edit Brand
            </CardTitle>
            <CardDescription className="text-base">
              Update your brand information and product images
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
                  required
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
                  required
                />
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label htmlFor="image1" className="text-sm font-medium">
                    Product Image 1 {image1 ? "(New)" : "(Current)"}
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
                    Product Image 2 {image2 ? "(New)" : "(Current)"}
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
                <GradientButton type="submit" disabled={loading} className="flex-1">
                  {loading ? "Updating..." : "Update Brand"}
                </GradientButton>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


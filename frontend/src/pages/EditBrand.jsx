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
  const [images, setImages] = useState([]) // Array of { file: File | null, preview: string | null, existingUrl: string | null }
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
        
        // Initialize with existing images
        const initialImages = []
        if (brand.product_image_1_url) {
          initialImages.push({
            file: null,
            preview: brand.product_image_1_url,
            existingUrl: brand.product_image_1_url
          })
        }
        if (brand.product_image_2_url) {
          initialImages.push({
            file: null,
            preview: brand.product_image_2_url,
            existingUrl: brand.product_image_2_url
          })
        }
        // If no existing images, start with 2 empty slots
        if (initialImages.length === 0) {
          initialImages.push({ file: null, preview: null, existingUrl: null })
          initialImages.push({ file: null, preview: null, existingUrl: null })
        }
        setImages(initialImages)
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

  const handleImageChange = (index, e) => {
    const file = e.target.files[0]
    if (file) {
      const newImages = [...images]
      newImages[index] = {
        ...newImages[index],
        file: file,
        preview: URL.createObjectURL(file)
      }
      setImages(newImages)
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
      
      // Append images - use product_image_1, product_image_2, etc.
      images.forEach((image, index) => {
        if (image.file) {
          formData.append(`product_image_${index + 1}`, image.file)
        }
      })

      await api.updateBrand(brandId, formData)
      // Navigate back to dashboard with state to force refresh
      navigate("/dashboard", { state: { refetch: true } })
    } catch (err) {
      // Extract error message from error object
      console.error('[EditBrand] Update failed:', err)
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

      // If authentication error, suggest re-login
      if (errorMessage.toLowerCase().includes('authenticated') || errorMessage.toLowerCase().includes('session')) {
        setError(errorMessage + ' - Please try logging out and logging back in.')
      }
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
                  Brand name:
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
                  Description:
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

              <div className="space-y-4">
                <label className="text-sm font-medium">Product Images</label>

                <div className="grid grid-cols-2 gap-6">
                  {images.slice(0, 2).map((image, index) => (
                    <div key={index} className="space-y-2">
                      <label htmlFor={`image${index}`} className="text-sm font-medium">
                        Product Image {index + 1} {image.file ? "(New)" : image.existingUrl ? "(Current)" : ""}
                      </label>
                      <div className="border-2 border-dashed rounded-lg p-6 text-center">
                        {image.preview ? (
                          <img
                            src={image.preview}
                            alt={`Preview ${index + 1}`}
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
                          id={`image${index}`}
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleImageChange(index, e)}
                          className="cursor-pointer"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-4 justify-end">
                <Button
                  type="button"
                  onClick={() => navigate("/dashboard")}
                  className="bg-red-500 hover:bg-red-600 text-white px-6 py-2 text-sm"
                >
                  Cancel
                </Button>
                <GradientButton type="submit" disabled={loading} className="!px-6 !py-2 !text-sm !min-w-0">
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


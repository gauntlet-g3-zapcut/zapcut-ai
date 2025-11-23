import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Textarea } from "../components/ui/textarea"
import { api } from "../services/api"
import { ImageUploader } from "../components/images"

export default function CreateBrand() {
  const navigate = useNavigate()
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [selectedImages, setSelectedImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleImagesSelected = (files) => {
    console.log('[CreateBrand] Images selected:', files.map(f => ({
      name: f.name,
      size: f.size,
      type: f.type,
      sizeInMB: (f.size / (1024 * 1024)).toFixed(2) + ' MB',
    })))
    setSelectedImages(files)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")

    if (!title || !description) {
      setError("Please fill in all fields")
      return
    }

    if (selectedImages.length < 2) {
      setError("Please upload at least 2 images")
      return
    }

    console.log('[CreateBrand] Submitting brand:', {
      title,
      descriptionLength: description.length,
      imageCount: selectedImages.length,
      images: selectedImages.map(img => ({
        name: img.name,
        size: img.size,
        type: img.type,
      })),
    })

    setLoading(true)

    try {
      // Step 1: Create brand with first 2 images (for backward compatibility)
      const formData = new FormData()
      formData.append("title", title)
      formData.append("description", description)
      formData.append("product_image_1", selectedImages[0])
      formData.append("product_image_2", selectedImages[1])

      console.log('[CreateBrand] Calling API to create brand...')
      const result = await api.createBrand(formData)
      console.log('[CreateBrand] Brand created successfully:', result)

      // Step 2: Upload additional images if there are more than 2
      if (selectedImages.length > 2) {
        const additionalImages = selectedImages.slice(2)
        console.log('[CreateBrand] Uploading additional images:', additionalImages.length)

        try {
          await api.uploadBrandImages(result.id, additionalImages)
          console.log('[CreateBrand] Additional images uploaded successfully')
        } catch (uploadErr) {
          console.error('[CreateBrand] Failed to upload additional images:', uploadErr)
          // Don't fail the whole operation, just warn
        }
      }

      // Navigate back to dashboard with state to force refresh
      navigate("/dashboard", { state: { refetch: true } })
    } catch (err) {
      // Extract error message from error object
      let errorMessage = "Failed to create brand"
      if (err.message) {
        errorMessage = err.message
      } else if (err.detail) {
        errorMessage = err.detail
      } else if (typeof err === "string") {
        errorMessage = err
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      }

      console.error('[CreateBrand] Failed to create brand:', {
        error: err,
        message: errorMessage,
      })
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
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
              Create Brand
            </CardTitle>
            <CardDescription className="text-base">
              Add your brand information and up to 10 product images to get started
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
                <label className="text-sm font-medium">
                  Product Images (Upload 2-10 images)
                </label>
                <ImageUploader
                  entityType="brand"
                  currentImageCount={0}
                  onFilesSelected={handleImagesSelected}
                  disabled={loading}
                />
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
                  {loading ? "Creating..." : "Create Brand"}
                </GradientButton>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Textarea } from "../components/ui/textarea"
import { api } from "../services/api"
import { ImageGallery, ImageCaptionModal, ImageUploader } from "../components/images"

export default function EditBrand() {
  const navigate = useNavigate()
  const { brandId } = useParams()
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [brand, setBrand] = useState(null)
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState("")
  const [selectedImage, setSelectedImage] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [showUploader, setShowUploader] = useState(false)

  const fetchBrand = async () => {
    try {
      setFetching(true)
      const brandData = await api.getBrand(brandId)
      setBrand(brandData)
      setTitle(brandData.title || "")
      setDescription(brandData.description || "")
    } catch (err) {
      setError(err.message || "Failed to load brand")
    } finally {
      setFetching(false)
    }
  }

  useEffect(() => {
    if (brandId) {
      fetchBrand()
    }
  }, [brandId])

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

      await api.updateBrand(brandId, formData)
      await fetchBrand() // Refresh brand data
      setError("")
    } catch (err) {
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
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteImage = async (imageId) => {
    if (!confirm("Are you sure you want to delete this image?")) {
      return
    }

    // Optimistic update: remove from local state immediately
    const currentImages = brand.images || []
    const imageToDelete = currentImages.find(img => img.id === imageId)
    const remainingImages = currentImages.filter(img => img.id !== imageId)

    // If deleting primary image, make first remaining image primary
    if (imageToDelete?.is_primary && remainingImages.length > 0) {
      remainingImages[0].is_primary = true
    }

    // Reorder remaining images
    remainingImages.forEach((img, index) => {
      img.order = index
    })

    setBrand(prev => ({
      ...prev,
      images: remainingImages
    }))

    try {
      await api.deleteBrandImage(brandId, imageId)
      // Success - local state already correct
    } catch (err) {
      // Revert on error
      setError(err.message || "Failed to delete image")
      setBrand(prev => ({
        ...prev,
        images: currentImages
      }))
    }
  }

  const handleEditImage = (imageId) => {
    const image = brand.images.find(img => img.id === imageId)
    setSelectedImage(image)
    setModalOpen(true)
  }

  const handleSetPrimary = async (imageId) => {
    // Optimistic update: update local state immediately
    const currentImages = brand.images || []

    // Find the image to make primary
    const targetImage = currentImages.find(img => img.id === imageId)
    if (!targetImage) return

    // Remove target image and unset all primary flags
    const otherImages = currentImages
      .filter(img => img.id !== imageId)
      .map(img => ({ ...img, is_primary: false }))

    // Put target image first with primary flag
    const updatedImages = [
      { ...targetImage, is_primary: true, order: 0 },
      ...otherImages.map((img, idx) => ({ ...img, order: idx + 1 }))
    ]

    setBrand(prev => ({
      ...prev,
      images: updatedImages
    }))

    try {
      await api.updateBrandImage(brandId, imageId, { is_primary: true })
      // Success - local state already correct
    } catch (err) {
      // Revert on error
      setError(err.message || "Failed to set primary image")
      setBrand(prev => ({
        ...prev,
        images: currentImages
      }))
    }
  }

  const handleReorder = async (imageIds) => {
    // Optimistic update: update local state immediately
    const currentImages = brand.images || []
    const imageMap = {}
    currentImages.forEach(img => {
      imageMap[img.id] = img
    })

    const reorderedImages = imageIds.map((id, index) => ({
      ...imageMap[id],
      order: index
    }))

    // Update local state immediately for smooth UX
    setBrand(prev => ({
      ...prev,
      images: reorderedImages
    }))

    // Send to server in background
    try {
      await api.reorderBrandImages(brandId, imageIds)
      // Success - local state already correct
    } catch (err) {
      // Revert on error
      setError(err.message || "Failed to reorder images")
      setBrand(prev => ({
        ...prev,
        images: currentImages
      }))
    }
  }

  const handleSaveImageMetadata = async (imageId, caption, isPrimary) => {
    // Optimistic update: update local state immediately
    const currentImages = brand.images || []
    const updatedImages = currentImages.map(img => {
      if (img.id === imageId) {
        return {
          ...img,
          caption,
          is_primary: isPrimary
        }
      }
      // If setting another image as primary, unset this one
      if (isPrimary && img.is_primary) {
        return {
          ...img,
          is_primary: false
        }
      }
      return img
    })

    setBrand(prev => ({
      ...prev,
      images: updatedImages
    }))

    try {
      await api.updateBrandImage(brandId, imageId, {
        caption,
        is_primary: isPrimary
      })
      // Success - local state already correct
    } catch (err) {
      // Revert on error
      setBrand(prev => ({
        ...prev,
        images: currentImages
      }))
      throw new Error(err.message || "Failed to update image")
    }
  }

  const handleUploadImages = async (files) => {
    try {
      setError("")
      await api.uploadBrandImages(brandId, files)
      await fetchBrand() // Refresh brand data
      setShowUploader(false)
    } catch (err) {
      setError(err.message || "Failed to upload images")
    }
  }

  const handleDeleteAll = async () => {
    const currentImages = brand.images || []

    // Optimistic update: clear images immediately
    setBrand(prev => ({
      ...prev,
      images: []
    }))

    try {
      // Delete all images one by one
      for (const image of currentImages) {
        await api.deleteBrandImage(brandId, image.id)
      }
      // Success - local state already correct
    } catch (err) {
      // Revert on error
      setError(err.message || "Failed to delete all images")
      setBrand(prev => ({
        ...prev,
        images: currentImages
      }))
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
      <div className="max-w-4xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6"
        >
          ← Back to Dashboard
        </Button>

        {/* Brand Info Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
              Edit Brand
            </CardTitle>
            <CardDescription className="text-base">
              Update your brand information
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

              <div className="flex gap-4 justify-end">
                <Button
                  type="button"
                  onClick={() => navigate("/dashboard")}
                  className="bg-red-500 hover:bg-red-600 text-white px-6 py-2 text-sm"
                >
                  Cancel
                </Button>
                <GradientButton type="submit" disabled={loading} className="!px-6 !py-2 !text-sm !min-w-0">
                  {loading ? "Updating..." : "Update Info"}
                </GradientButton>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Image Management Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-bold">
              Product Images
            </CardTitle>
            <CardDescription className="text-base">
              Manage your brand images (up to 10 total)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {showUploader ? (
              <div className="space-y-4">
                <ImageUploader
                  entityType="brand"
                  currentImageCount={brand?.images?.length || 0}
                  onFilesSelected={handleUploadImages}
                  maxImages={10}
                />
                <Button
                  variant="ghost"
                  onClick={() => setShowUploader(false)}
                  className="w-full"
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <ImageGallery
                images={brand?.images || []}
                maxImages={10}
                entityType="brand"
                onDelete={handleDeleteImage}
                onImageClick={handleEditImage}
                onSetPrimary={handleSetPrimary}
                onReorder={handleReorder}
                onAddMore={() => setShowUploader(true)}
                onDeleteAll={handleDeleteAll}
              />
            )}
          </CardContent>
        </Card>

        {/* Image Caption Modal */}
        <ImageCaptionModal
          image={selectedImage}
          isOpen={modalOpen}
          onClose={() => {
            setModalOpen(false)
            setSelectedImage(null)
          }}
          onSave={handleSaveImageMetadata}
        />
      </div>
    </div>
  )
}

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
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
      console.log('[CreateBrand] Image 1 selected:', {
        name: file.name,
        size: file.size,
        type: file.type,
        sizeInMB: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
      })
      setImage1(file)
      setPreview1(URL.createObjectURL(file))
    }
  }

  const handleImage2Change = (e) => {
    const file = e.target.files[0]
    if (file) {
      console.log('[CreateBrand] Image 2 selected:', {
        name: file.name,
        size: file.size,
        type: file.type,
        sizeInMB: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
      })
      setImage2(file)
      setPreview2(URL.createObjectURL(file))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")

    if (!title || !description || !image1 || !image2) {
      setError("Please fill in all fields and upload both images")
      return
    }

    console.log('[CreateBrand] Submitting brand:', {
      title,
      descriptionLength: description.length,
      image1: {
        name: image1.name,
        size: image1.size,
        type: image1.type,
      },
      image2: {
        name: image2.name,
        size: image2.size,
        type: image2.type,
      },
    })

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append("title", title)
      formData.append("description", description)
      formData.append("product_image_1", image1)
      formData.append("product_image_2", image2)

      console.log('[CreateBrand] Calling API to create brand...')
      const result = await api.createBrand(formData)
      console.log('[CreateBrand] Brand created successfully:', result)

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
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
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
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
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
                        required
                      />
                    </div>
                  </div>
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


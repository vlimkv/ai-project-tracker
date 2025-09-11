group "default" {
  targets = ["backend", "web", "bot", "llm"]
}

variable "IMAGE_PREFIX" {
  default = "ghcr.io/owner/repo"
}

target "common" {
  platforms = ["linux/amd64"]
}

target "backend" {
  inherits = ["common"]
  context = "./backend"
  dockerfile = "Dockerfile"
  tags = ["${IMAGE_PREFIX}/backend:latest"]
}

target "web" {
  inherits = ["common"]
  context = "./web"
  dockerfile = "Dockerfile"
  tags = ["${IMAGE_PREFIX}/web:latest"]
}

target "bot" {
  inherits = ["common"]
  context = "./bot"
  dockerfile = "Dockerfile"
  tags = ["${IMAGE_PREFIX}/bot:latest"]
}

target "llm" {
  inherits = ["common"]
  context = "."
  dockerfile = "llm.Dockerfile"
  tags = ["${IMAGE_PREFIX}/llm:latest"]
}
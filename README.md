BBC Scraper and Flask App Project

Projekt na potrzeby studiów/ uni projekt
Installation and Usage

    Clone the repository:
    git clone <repository_url>
    cd Projekt20502
    Make sure you have either Docker-compose or minikube & kubectl installed

Run the Docker containers:
    
    Dla docker compose
        docker-compose build
        docker-compose up
    Dla kubernetes
        cd scraper
        docker build -t <docker-username>/scraper:latest -f Dockerfile.scraper .
        cd ../web_app
        docker build -t <docker-username>/webapp:latest -f Dockerfile .
        cd ../kubernetes
        Zedytuj zawartość plików kubernetes(szczególnie image: your-webapp-image:tag )
        kubectl apply -f kubernetes/mongodb_pv.yaml
        kubectl apply -f kubernetes/mongodb_pvc.yaml
        kubectl apply -f kubernetes/mongodb_deployment.yaml
        kubectl apply -f kubernetes/scraper_deployment.yaml
        kubectl apply -f kubernetes/webapp_deployment.yaml
        kubectl apply -f kubernetes/webapp_service.yaml

        
Access the web application:

    For docker compose
    Open your browser and navigate to http://localhost:5000.
    For kubernetes
    kubectl get services
    kubectl get svc <nazwa serwisu webapp>
    minikube service  <nazwa serwisu webapp>

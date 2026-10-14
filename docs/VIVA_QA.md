# FieldMind: Viva Voce Q&A Guide

**Q1: Why did you choose this project?**
**A:** We wanted to solve practical problems in agriculture using technology. Existing solutions are fragmented. We built a unified platform that not only detects crop diseases using ML but also provides crop recommendations and a peer-to-peer marketplace for renting equipment and hiring labor.

**Q2: Why did you use FastAPI for the backend?**
**A:** FastAPI is highly performant, supports asynchronous programming out-of-the-box, and automatically generates API documentation (Swagger). The async support was critical for handling non-blocking ML inference and database operations simultaneously.

**Q3: Why React and Vite for the frontend?**
**A:** React allows for modular, component-based UI development. Vite was chosen over Create React App because its build process and hot-module-reloading are significantly faster, providing a much better developer experience.

**Q4: Why use Firebase/Firestore?**
**A:** Firebase provides a managed, secure authentication system. Firestore is a NoSQL document database that allows for highly flexible schemas, which was ideal for storing unstructured data like marketplace listings and varying ML diagnosis results without complex migrations.

**Q5: Why use ONNX (Open Neural Network Exchange)?**
**A:** ONNX allows us to train models in frameworks like PyTorch or TensorFlow, export them, and run them efficiently in a standardized runtime (`onnxruntime`). It decouples the inference engine from the training framework, making our backend lighter and faster.

**Q6: What is the LeafVerifier?**
**A:** It is a binary classification ML model executed *before* the main disease classifier. Its sole job is to determine if the uploaded image actually contains a plant leaf. 

**Q7: Why have a LeafVerifier before disease classification?**
**A:** To prevent the "garbage in, garbage out" problem. The disease classifier expects a leaf and does not have an "Unknown" class. If a user uploads a picture of a car, the disease classifier would force a guess (e.g., predicting Maize Blight). The LeafVerifier creates a "Fail-Fast" architecture, rejecting non-leaves early, saving compute resources, and preserving user trust.

**Q8: What is the purpose of blur detection?**
**A:** We use OpenCV's Laplacian variance to calculate a blur score. If an image is too blurry, the ML models cannot extract meaningful features, leading to random guesses. By stopping the pipeline at the validation stage, we ensure only high-quality data reaches the models.

**Q9: What happens when the image is not a leaf?**
**A:** The LeafVerifier outputs a high confidence that it is a "non_leaf". The backend immediately aborts the pipeline, sets the status to "rejected," and returns a friendly error message to the frontend asking the user to upload a valid leaf image. The Disease Classifier is never executed.

**Q10: What is asynchronous inference?**
**A:** It means the ML model processing does not block the main web server thread. The request is pushed to a background worker queue (using RQ/Redis or async tasks), allowing the FastAPI server to continue handling other users' requests while the heavy ML math computes in the background.

**Q11: Why use YOLO?**
**A:** YOLO (You Only Look Once) is an object detection model. While the Disease Classifier tells us *what* the disease is, YOLO tells us *where* it is by drawing bounding boxes around the severity/pest areas, giving the farmer a visual confirmation of the problem.

**Q12: How does authentication work?**
**A:** We use Firebase Authentication on the frontend to handle secure login (Email/Password or Google). The frontend receives a JWT token, which is passed in the headers to the FastAPI backend. The backend verifies this token with Firebase Admin SDK to ensure the request is authorized.

**Q13: How does the marketplace work?**
**A:** Users can create equipment or worker profiles. These are stored in Firestore. Other users can initiate a "Booking" document linking the requester and the owner. The owner can then change the booking status (Pending -> Approved -> Completed).

**Q14: What testing was performed?**
**A:** We wrote 99 automated backend tests using `pytest` covering authentication, endpoints, health checks, and mock ML pipelines. We also performed an End-to-End ML evaluation to verify that blurry and non-leaf images are correctly rejected by the pipeline.

**Q15: What are the limitations of your project?**
**A:** Currently, we lack a large, verified ground-truth dataset for our 22 disease classes, so we cannot scientifically prove the exact accuracy percentage of the disease classifier. Also, the YOLO model operates independently from the classifier, which can sometimes result in mismatched bounding box labels.

**Q16: Tell us about the LeafVerifier V3 experiment.**
**A:** We noticed the production V2 LeafVerifier occasionally struggled with ambiguous images. As an ML engineering exercise, we designed a V3 dataset policy (strictly Leaf vs Non-Leaf), created a new dataset of ~1,400 images, and trained a new PyTorch EfficientNet-B0 model. We achieved ~97.8% test accuracy locally. We kept V2 in production for stability but documented the V3 pipeline to show our ML lifecycle capability.

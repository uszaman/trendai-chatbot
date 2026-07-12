# Setup Runbook — TrendAI Chatbot on AWS

End-to-end steps to stand up the whole stack for the demo. Budget ~$3–5 in AWS
if you tear it down the same day.

## 0. Prerequisites
- AWS account + `aws` CLI configured (`aws configure`)
- `terraform`, `kubectl`, `docker`, `git` installed
- An EC2 key pair name (create in the console if needed)

## 1. Provision infrastructure (Task 1)
```bash
cd terraform
terraform init
terraform apply \
  -var="ssh_key_name=YOUR_KEYPAIR" \
  -var="my_ip_cidr=$(curl -s ifconfig.me)/32"
```
Note the outputs: `k3s_public_ip` and `backup_bucket`.

## 2. Get kubeconfig from the k3s node
```bash
#IP=<k3s_public_ip>
IP=13.212.24.150
ssh ubuntu@$IP "sudo cat /etc/rancher/k3s/k3s.yaml" > kubeconfig

UZ:
ssh -i trendai-chatbot.pem ubuntu@13.212.24.150 "sudo cat /etc/rancher/k3s/k3s.yaml" > kubeconfig

Then had to remove rights on the pem to for Built in User and Auth Users.  (i did manually, but claud gave below)
icacls "C:\path\to\your-key.pem" /inheritance:r
icacls "C:\path\to\your-key.pem" /grant:r "$($env:USERNAME):(R)"


# point it at the public IP instead of 127.0.0.1
#sed -i "s/127.0.0.1/$IP/" kubeconfig
sed -i "s/13.212.24.150/$IP/" kubeconfig
export KUBECONFIG=$PWD/kubeconfig
kubectl get nodes        # should show the node Ready
```

UZ: For powershell:
$env:KUBECONFIG = "$PWD\kubeconfig"
kubectl get nodes

Gives cert error because cert is only for internal IP not public.

ssh -i trendai-chatbot.pem ubuntu@13.212.24.150
curl -sfL https://get.k3s.io | sudo INSTALL_K3S_EXEC="--tls-san 13.212.24.150" sh -
exit

--> Then re-pull the kubeconfig and swap 127.0.0.1 for the public IP again. This regenerates the cert with the public IP as a valid Subject Alternative Name.

--> Worth knowing for the interview: this is a real-world manifestation of the TLS gap in your analysis. If they ask about certificate management, you’ve now actually hit the problem — certs must be issued for the name/IP clients actually use. That’s a credible thing to mention.

--> I’d take the quick fix now and keep moving. Once kubectl get nodes shows Ready, you’re on to Step 3 (namespace + secrets).


PS C:\tm\trendai-chatbot\terraform> $env:KUBECONFIG = "$PWD\kubeconfig"
PS C:\tm\trendai-chatbot\terraform> kubectl get nodes
NAME           STATUS   ROLES           AGE   VERSION
ip-10-0-1-24   Ready    control-plane   42m   v1.36.2+k3s1
PS C:\tm\trendai-chatbot\terraform>



## 3. Create namespace and secrets (never commit these)
```bash
kubectl apply -f k8s/frontend.yaml   # creates the namespace first
kubectl create secret generic mongo-secret -n chatbot \
  --from-literal=username=admin \
  --from-literal=password="$(openssl rand -base64 16)" \
  --from-literal=uri="mongodb://admin:PASSWORD@mongodb:27017/chatbot?authSource=admin"
kubectl create secret generic llm-secret -n chatbot \
  --from-literal=api-key="sk-ant-..."
```
(Use the same password in the URI.)

UZ-----------------
PS C:\tm\trendai-chatbot\terraform> kubectl apply -f ..\k8s\frontend.yaml
namespace/chatbot created
deployment.apps/frontend created
service/frontend created
Warning: annotation "kubernetes.io/ingress.class" is deprecated, please use 'spec.ingressClassName' instead
ingress.networking.k8s.io/chatbot-ingress created


#$PW = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | % {[char]$_})
$PW = "Par0wan@Jala"
kubectl create secret generic mongo-secret -n chatbot `
  --from-literal=username=admin `
  --from-literal=password="$PW" `
  --from-literal=uri="mongodb://admin:$PW@mongodb:27017/chatbot?authSource=admin"

kubectl create secret generic llm-secret -n chatbot `

PS C:\tm\trendai-chatbot\terraform> $PW = "Par0wan@Jala"
PS C:\tm\trendai-chatbot\terraform> kubectl create secret generic mongo-secret -n chatbot `
>>   --from-literal=username=admin `
>>   --from-literal=password="$PW" `
>>   --from-literal=uri="mongodb://admin:$PW@mongodb:27017/chatbot?authSource=admin"
secret/mongo-secret created
PS C:\tm\trendai-chatbot\terraform>
PS C:\tm\trendai-chatbot\terraform> kubectl create secret generic llm-secret -n chatbot `
secret/llm-secret created


C:\tm\trendai-chatbot\terraform>kubectl apply -f ..\k8s\frontend.yaml
error: error validating "..\\k8s\\frontend.yaml": error validating data: failed to download openapi: Get "http://localhost:8080/openapi/v2?timeout=32s": dial tcp [::1]:8080: connectex: No connection could be made because the target machine actively refused it.; if you choose to ignore these errors, turn validation off with --validate=false


kubectl apply -f ..\k8s\mongodb.yaml
kubectl get pods -n chatbot

NAME                        READY   STATUS             RESTARTS   AGE
frontend-5894b5f78c-2bntp   0/1     ImagePullBackOff   0          18m
frontend-5894b5f78c-7g7q8   0/1     ImagePullBackOff   0          18m
mongodb-6c9d68c658-7ct6f    1/1     Running            0          44s


Push to GitHub - https://github.com/uszaman/trendai-chatbot
cd C:\tm\trendai-chatbot
git init
git branch -M main
git add .
git commit -m "TrendAI chatbot: infra, app, k8s, CI/CD"
git remote add origin https://github.com/uszaman/trendai-chatbot.git
git push -u origin main

Secrets were present, so push got blocked.
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - GITHUB PUSH PROTECTION
remote:   —————————————————————————————————————————
remote:     Resolve the following violations before pushing again
remote:
remote:     - Push cannot contain secrets
remote:
remote:
remote:      (?) Learn how to resolve a blocked push
remote:      https://docs.github.com/code-security/secret-scanning/working-with-secret-scanning-and-push-protection/working-with-push-protection-from-the-command-line#resolving-a-blocked-push
remote:
remote:
remote:       —— Anthropic API Key —————————————————————————————————
remote:        locations:
remote:          - commit: 03d8da0a109549f1fbdea3cd3c7c0f17d39ef742
remote:            path: SETUP.md:96
remote:          - commit: 03d8da0a109549f1fbdea3cd3c7c0f17d39ef742
remote:            path: SETUP.md:106
remote:
remote:        (?) To push, remove secret from commit(s) or follow this URL to allow the secret.
remote:        https://github.com/uszaman/trendai-chatbot/security/secret-scanning/unblock-secret/3GOXVdZceYs1tm9NaaLVOKDJoOC
remote:
remote:
remote:
To https://github.com/uszaman/trendai-chatbot.git
 ! [remote rejected] main -> main (push declined due to repository rule violations)
error: failed to push some refs to 'https://github.com/uszaman/trendai-chatbot.git'


Worth noting: terraform.tfstate contains your MongoDB password and other secrets in plaintext. Getting it out of the repo isn’t just about file size — it’s exactly the kind of thing Gitleaks exists to catch. If it had gone up, that’s a real finding against you in a security interview.

## 4. Build & push images
```bash
# Using GitHub Container Registry (ghcr.io)
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
docker build -t ghcr.io/USER/chatbot-backend:latest backend/ && docker push ghcr.io/USER/chatbot-backend:latest
docker build -t ghcr.io/USER/chatbot-frontend:latest frontend/ && docker push ghcr.io/USER/chatbot-frontend:latest
# update the image: lines in k8s/backend.yaml and k8s/frontend.yaml
```

## 5. Deploy the app (Task 2)
```bash
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl get pods -n chatbot          # all should reach Running
```
Open `http://<k3s_public_ip>/` in a browser — type a message, get a reply.

## 6. Backups (Task 3)
```bash
kubectl apply -f k8s/backup-cronjob.yaml
# force one run to prove it works instead of waiting 24h:
kubectl create job -n chatbot --from=cronjob/mongodb-backup manual-backup-1
kubectl logs -n chatbot job/manual-backup-1
aws s3 ls s3://<backup_bucket>/mongodb/   # backup file should appear
```

## 7. CI/CD (Task 4)
- Push the repo to GitHub.
- Add repo secrets: `KUBECONFIG_B64` (`base64 -w0 kubeconfig`), any registry creds.
- Every push to `main` runs Gitleaks + ruff + Trivy, then builds and deploys.
- Show the green pipeline run in the Actions tab during the demo.

## 8. Teardown (after the interview)
```bash
kubectl delete namespace chatbot
cd terraform && terraform destroy -var="ssh_key_name=YOUR_KEYPAIR" -var="my_ip_cidr=$(curl -s ifconfig.me)/32"
```

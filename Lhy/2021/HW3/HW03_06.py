# Import necessary packages.
import time
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
# "ConcatDataset" and "Subset" are possibly useful when doing semi-supervised learning.
from torch.utils.data import ConcatDataset, DataLoader, Subset
from torchvision.datasets import DatasetFolder

# This is for the progress bar.
from tqdm.auto import tqdm

# It is important to do images augmentation in training.
# However, not every augmentation is useful.
# Please think about what kind of augmentation is helpful for food recognition.
train_tfm = transforms.Compose([
    # Resize the image into a fixed shape (height = width = 128)
    transforms.Resize((128, 128)),
    # You may add some transforms here.
    # ToTensor() should be the last one of the transforms.
    transforms.RandomCrop(128, padding=4),  # 先四周填充0，在吧图像随机裁剪成32*32
    transforms.RandomHorizontalFlip(),  # 图像一半的概率翻转，一半的概率不翻转

    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),

])

# We don't need augmentations in testing and validation.
# All we need here is to resize the PIL image and transform it into Tensor.
test_tfm = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),

])

# Batch size for training, validation, and testing.
# A greater batch size usually gives a more stable gradient.
# But the GPU memory is limited, so please adjust it carefully.
batch_size = 128

# Construct datasets.
# The argument "loader" tells how torchvision reads the images.
train_set = DatasetFolder("../images/food-11/training/labeled", loader=lambda x: Image.open(x), extensions="jpg",
                          transform=train_tfm)
valid_set = DatasetFolder("../images/food-11/validation", loader=lambda x: Image.open(x), extensions="jpg",
                          transform=test_tfm)
# unlabeled_set = DatasetFolder("../images/food-11/training/unlabeled", loader=lambda x: Image.open(x), extensions="jpg", transform=test_tfm)
unlabeled_set = DatasetFolder("../images/food-11/training/unlabeled", loader=lambda x: Image.open(x), extensions="jpg",
                              transform=train_tfm)
test_set = DatasetFolder("../images/food-11/testing", loader=lambda x: Image.open(x), extensions="jpg",
                         transform=test_tfm)

# Construct images loaders.
train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
valid_loader = DataLoader(valid_set, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)
unlabel_loader = DataLoader(unlabeled_set, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)


class Classifier(nn.Module):
    def __init__(self):
        super(Classifier, self).__init__()
        # The arguments for commonly used modules:
        # torch.nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding)
        # torch.nn.MaxPool2d(kernel_size, stride, padding)

        # input image size: [3, 128, 128]
        self.cnn_layers = nn.Sequential(
            nn.Conv2d(3, 64, 3, 1, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2, 0),

            nn.Conv2d(64, 128, 3, 1, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2, 0),

            nn.Conv2d(128, 256, 3, 1, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(4, 4, 0),
        )
        self.fc_layers = nn.Sequential(
            nn.Linear(256 * 8 * 8, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 11)
        )

    def forward(self, x):
        # input (x): [batch_size, 3, 128, 128]
        # output: [batch_size, 11]

        # Extract features by convolutional layers.
        x = self.cnn_layers(x)

        # The extracted feature map must be flatten before going to fully-connected layers.
        x = x.flatten(1)

        # The features are transformed by fully-connected layers to obtain the final logits.
        x = self.fc_layers(x)
        return x


def calc_ent(x):
    """
        calculate shanno ent of x
    """
    x_value_list = set([x[i] for i in range(x.shape[0])])
    ent = 0.0
    for x_value in x_value_list:
        p = float(x[x == x_value].shape[0]) / x.shape[0]
        logp = np.log2(p)
        ent -= p * logp

    return ent


all_target = []


def get_pseudo_labels(model, unlable_dataset, semi_dataset, threshold=0.650):
    # This functions generates pseudo-labels of a dataset using given model.
    # It returns an instance of DatasetFolder containing images whose prediction confidences exceed a given threshold.
    # You are NOT allowed to use any models trained on external images for pseudo-labeling.
    # Make sure the model is in eval mode.
    # train_set = DatasetFolder("../images/food-11/training/labeled", loader=lambda x: Image.open(x), extensions="jpg",
    #                           transform=train_tfm)
    # semi_dataset = DatasetFolder("../images/food-11/training/labeled",loader=lambda x: Image.open(x), extensions="jpg", transform=train_tfm)
    # unlabeled_dataset =  DatasetFolder("../images/food-11/training/labeled",loader=lambda x: Image.open(x), extensions="jpg", transform=train_tfm)
    unlabeled_loader = DataLoader(unlable_dataset, batch_size=batch_size,
                                  shuffle=True, num_workers=2, pin_memory=False)

    model.eval()
    # Define softmax function.
    # softmax = nn.Softmax(dim=-1)
    softmax = nn.Softmax(dim=0)
    labels = []
    targets = []
    # Iterate over the dataset by batches.
    # for batch in tqdm(dataloader):
    for batch in tqdm(unlabeled_loader):
        img, _ = batch
        # Forward the images
        # Using torch.no_grad() accelerates the forward process.
        with torch.no_grad():
            logits = model(img.to(device))
            # logits = torch.rand(128, 11)

            # Obtain the probability distributions by applying softmax on logits.
            probs = softmax(logits)

            # ---------- TODO ----------
            # Filter the images and construct a new dataset.
            # probs = probs[probs.max(dim=1) > threshold]
            # print(probs.max(dim=1))
            # print(probs.max(dim=1)[0] > threshold)
            # print(probs[probs.max(dim=1)[0] > threshold])
            # probs_b = [probs.max(dim=1)[0] > threshold]
            probs_max = probs.max(dim=1)
            probs_max_0 = probs_max[0]
            probs_b = [probs_max_0 > threshold]
            probs = probs[probs_b]
            # probs = probs[probs_b]
            # print(len(targets))
            # print(len(probs_b))

            targets = targets + probs_b[0].cpu().numpy().tolist()
            if probs.shape[0] > 0:
                # print(probs)
                img_label = torch.argmax(probs, dim=1).to(device)
                # labels = torch.cat([labels, img_label], dim=0).to(device)
                labels += img_label.cpu().numpy().tolist()
                # print(torch.argmax(probs, dim=1))

    # # Turn off the eval mode.
    # model.train()
    print(type(targets))
    print(type(labels))
    print(len(targets))
    print(len(labels))
    semi_samples = []
    unlabel_samples = []
    li = 0
    for i, e in enumerate(targets):
        if e:
            semi_samples.append((unlabel_dataset.samples[i][0], labels[li]))
            li += 1
        else:
            unlabel_samples.append(unlabel_dataset.samples[i])
    semi_dataset.samples += semi_samples
    semi_dataset.targets += [i[1] for i in semi_samples]
    unlabel_dataset.samples = unlabel_samples
    unlabel_dataset.targets = [0] * len(unlabel_samples)
    model.train()
    return semi_dataset


# "cuda" only when GPUs are available.
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = torch.device("cpu")

# Initialize a model, and put it on the device specified.
model = Classifier().to(device)
model.device = device

# For the classification task, we use cross-entropy as the measurement of performance.
criterion = nn.CrossEntropyLoss()

# Initialize optimizer, you may fine-tune some hyperparameters such as learning rate on your own.
optimizer = torch.optim.Adam(model.parameters(), lr=0.0003, weight_decay=1e-5)

# The number of training epochs.
n_epochs = 400

# Whether to do semi-supervised learning.
# do_semi = False
do_semi = True
semi_pi = 0.1
semi_dataset = DatasetFolder("../images/food-11/training/labeled", loader=lambda x: Image.open(x), extensions="jpg",
                             transform=train_tfm)
semi_dataset.samples = []
semi_dataset.targets = []
unlabel_dataset =  DatasetFolder("../images/food-11/training/unlabeled", loader=lambda x: Image.open(x), extensions="jpg",
                              transform=train_tfm)

for epoch in range(n_epochs):
    # ---------- TODO ----------
    # In each epoch, relabel the unlabeled dataset for semi-supervised learning.
    # Then you can combine the labeled dataset and pseudo-labeled dataset for the training.
    if do_semi:
        # Obtain pseudo-labels for unlabeled images using trained model.
        pseudo_set = get_pseudo_labels(model, unlabel_dataset, semi_dataset)
        # Construct a new dataset and a images loader for training.
        # This is used in semi-supervised learning only.
        # concat_dataset = ConcatDataset([train_set, pseudo_set])
        concat_dataset = ConcatDataset([pseudo_set, train_set])
        train_loader = DataLoader(concat_dataset, batch_size=batch_size, shuffle=True, num_workers=1, pin_memory=False,
                                  drop_last=True)

    # ---------- Training ----------
    # Make sure the model is in train mode before training.
    model.train()

    # These are used to record information in training.
    train_loss = []
    train_accs = []

    # Iterate the training set by batches.
    for batch in tqdm(train_loader):
        # A batch consists of image images and corresponding labels.
        imgs, labels = batch
        # Forward the images. (Make sure images and model are on the same device.)
        logits = model(imgs.to(device))

        # Calculate the cross-entropy loss.
        # We don't need to apply softmax before computing cross-entropy as it is done automatically.
        loss = criterion(logits, labels.to(device)) + semi_pi * calc_ent(logits)

        # Gradients stored in the parameters in the previous step should be cleared out first.
        optimizer.zero_grad()

        # Compute the gradients for parameters.
        loss.backward()

        # Clip the gradient norms for stable training.
        grad_norm = nn.utils.clip_grad_norm_(model.parameters(), max_norm=10)

        # Update the parameters with computed gradients.
        optimizer.step()

        # Compute the accuracy for current batch.
        acc = (logits.argmax(dim=-1) == labels.to(device)).float().mean()

        # Record the loss and accuracy.
        train_loss.append(loss.item())
        train_accs.append(acc)

    # The average loss and accuracy of the training set is the average of the recorded values.
    train_loss = sum(train_loss) / len(train_loss)
    train_acc = sum(train_accs) / len(train_accs)

    # Print the information.
    now = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime())
    print(f"{now}[ Train | {epoch + 1:03d}/{n_epochs:03d} ] loss = {train_loss:.5f}, acc = {train_acc:.5f}")

    # ---------- Validation ----------
    # Make sure the model is in eval mode so that some modules like dropout are disabled and work normally.
    model.eval()

    # These are used to record information in validation.
    valid_loss = []
    valid_accs = []

    # Iterate the validation set by batches.
    for batch in tqdm(valid_loader):
        # A batch consists of image images and corresponding labels.
        imgs, labels = batch
        # We don't need gradient in validation.
        # Using torch.no_grad() accelerates the forward process.
        with torch.no_grad():
            logits = model(imgs.to(device))

        # We can still compute the loss (but not the gradient).
        loss = criterion(logits, labels.to(device))

        # Compute the accuracy for current batch.
        acc = (logits.argmax(dim=-1) == labels.to(device)).float().mean()

        # Record the loss and accuracy.
        valid_loss.append(loss.item())
        valid_accs.append(acc)

    # The average loss and accuracy for entire validation set is the average of the recorded values.
    valid_loss = sum(valid_loss) / len(valid_loss)
    valid_acc = sum(valid_accs) / len(valid_accs)
    # Print the information.
    now = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime())
    print(f"{now}[Valid | {epoch + 1:03d}/{n_epochs:03d} ] loss = {valid_loss:.5f}, acc = {valid_acc:.5f}")

# Make sure the model is in eval mode.
# Some modules like Dropout or BatchNorm affect if the model is in training mode.
model.eval()

# Initialize a list to store the predictions.
predictions = []

# Iterate the testing set by batches.
for batch in tqdm(test_loader):
    # A batch consists of image images and corresponding labels.
    # But here the variable "labels" is useless since we do not have the ground-truth.
    # If printing out the labels, you will find that it is always 0.
    # This is because the wrapper (DatasetFolder) returns images and labels for each batch,
    # so we have to create fake labels to make it work normally.
    imgs, labels = batch
    # We don't need gradient in testing, and we don't even have labels to compute loss.
    # Using torch.no_grad() accelerates the forward process.
    with torch.no_grad():
        logits = model(imgs.to(device))

    # Take the class with greatest logit as prediction and record it.
    predictions.extend(logits.argmax(dim=-1).cpu().numpy().tolist())
# Save predictions into the file.
with open("predict.csv", "w") as f:
    # The first row must be "Id, Category"
    f.write("Id,Category\n")

    # For the rest of the rows, each image id corresponds to a predicted class.
    for i, pred in enumerate(predictions):
        f.write(f"{i},{pred}\n")

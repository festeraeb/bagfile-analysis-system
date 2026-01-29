#!/usr/bin/env python3
"""Quick fine-tune including the NAmag grid patches as background samples."""
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import sys, os
repo_root = os.getcwd()
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'magnetic_data', 'ai4shipwrecks_repo', 'noaa_mbes_shipwreckfinder_model-main'))
from models.unet_aux.unet_aux import UnetAux

TRAIN_DIRS = [Path('training/synthetic_mbess'), Path('training/synthetic_mag'), Path('training/ai4shipwrecks_patches'), Path('training/grids/namag_origmrg_for_training')]
OUT_MODEL = Path('training/models/unet_finetuned_with_namag.pt')
BATCH_SIZE = 8
EPOCHS = 2
LR = 1e-4
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
TILE_SIZE = 256

class PatchDataset(Dataset):
    def __init__(self, dirs, tile_size=256):
        self.files = []
        for d in dirs:
            d = Path(d)
            if not d.exists():
                continue
            for f in d.glob('*_image.npy'):
                lab = d / (f.stem.replace('_image','_label') + '.npy')
                if lab.exists():
                    self.files.append((f, lab))
        self.tile_size = tile_size

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        f, l = self.files[idx]
        img = np.load(f)
        lab = np.load(l)
        if img.ndim == 2:
            img = np.expand_dims(img,0)
        if img.shape[1] != self.tile_size or img.shape[2] != self.tile_size:
            h,w = img.shape[1:]
            if h >= self.tile_size and w >= self.tile_size:
                sh = (h - self.tile_size)//2
                sw = (w - self.tile_size)//2
                img = img[:, sh:sh+self.tile_size, sw:sw+self.tile_size]
                lab = lab[sh:sh+self.tile_size, sw:sw+self.tile_size]
            else:
                pad_h = max(0, self.tile_size - h)
                pad_w = max(0, self.tile_size - w)
                img = np.pad(img, ((0,0),(0,pad_h),(0,pad_w)), mode='constant')
                lab = np.pad(lab, ((0,pad_h),(0,pad_w)), mode='constant')
                img = img[:, :self.tile_size, :self.tile_size]
                lab = lab[:self.tile_size, :self.tile_size]
        img = (img - np.nanmean(img)) / (np.nanstd(img) + 1e-9)
        img = np.nan_to_num(img).astype(np.float32)
        lab = (lab > 0).astype(np.int64)
        return {'image': torch.from_numpy(img), 'label': torch.from_numpy(lab)}


def collate_fn(batch):
    images = torch.stack([b['image'] for b in batch])
    labels = torch.stack([b['label'] for b in batch])
    return images, labels


def main():
    ds = PatchDataset(TRAIN_DIRS, tile_size=TILE_SIZE)
    if len(ds) == 0:
        print('No training patches found. Exiting.')
        return
    print('Dataset size:', len(ds))
    dl = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn, num_workers=2)

    model = UnetAux(1,2)
    model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    ce = torch.nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        model.train()
        pbar = tqdm(dl, desc=f'Epoch {epoch+1}/{EPOCHS}')
        losses = []
        for images, labels in pbar:
            images = images.to(DEVICE).float()
            if images.ndim == 3:
                images = images.unsqueeze(1)
            if images.shape[1] != 1:
                images = images[:, :1, ...]
            labels = labels.to(DEVICE).long()

            opt.zero_grad()
            out = model(images)
            loss = ce(out, labels)
            loss.backward(); opt.step()
            losses.append(loss.item())
            pbar.set_postfix(loss=f'{np.mean(losses):.4f}')

    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(OUT_MODEL))
    print('Saved fine-tuned model to', OUT_MODEL)

if __name__ == '__main__':
    main()

# 🔐 Supabase Credentials Setup Guide

## Your Supabase Configuration

Your Factor-Lake project is configured to use Supabase with these credentials: 

- **URL:** `https://-----.supabase.co`
- **Key:** `sb_publishable_-----`

## ✅ Setup Complete!

Your credentials are now configured in **three places**:

### 1. **Local Development** (`.env` file)
- Location: `Factor-Lake_2/.env`
- Used when running locally with `python run_streamlit.py`
- **Protected by .gitignore** - won't be committed to GitHub

### 2. **Streamlit App** (`streamlit_app.py`)
- Automatically loads credentials from `.env` file
- No code changes needed when running locally

### 3. **Google Colab** (`colab_setup.ipynb`)
- Credentials are set directly in the notebook
- Ready to use when deployed to Colab

## 🚀 How to Use

### Running Locally:
```bash
# Just run the app - credentials load automatically from .env
python run_streamlit.py
```

### Running on Google Colab:
1. Open `colab_setup.ipynb` in Google Colab
2. Run all cells - credentials are already configured
3. Access via the ngrok URL

### In the Streamlit App:
1. In the sidebar, select **"Supabase (Cloud)"** as data source
2. Click **"Load Data"**
3. Data loads automatically using your credentials

## 🔒 Security Notes

✅ **Local `.env` file** - Protected by .gitignore (won't push to GitHub)  
✅ **Supabase key is publishable** - Safe to use on client-side  
⚠️ **Colab notebook currently outdated** - Contains credentials, but that's OK for personal use  

If you need to share the project publicly:
- Keep the `.env` file local only
- Remove credentials from `colab_setup.ipynb` before sharing
- Ask users to add their own credentials

## 🛠️ Changing Credentials

If you need to update your credentials:

1. **Edit `.env` file:**
   ```env
   SUPABASE_URL=your-new-url
   SUPABASE_KEY=your-new-key
   ```

2. **Restart the Streamlit app** - it will load the new credentials

## 📋 Verification

To verify your credentials are working:

1. Start the app: `python run_streamlit.py`
2. Select "Supabase (Cloud)" in the sidebar
3. Click "Load Data"
4. If successful, you'll see: "✅ Data loaded successfully!"

## 🆘 Troubleshooting

### "Connection failed" error:
- Check your internet connection
- Verify the Supabase URL is correct
- Ensure your Supabase project is active

### "Authentication failed" error:
- Verify the SUPABASE_KEY is correct
- Check if the key has expired
- Try regenerating the key in Supabase dashboard

### App can't find .env file:
- Make sure `.env` is in the root directory (same level as `streamlit_app.py`)
- Check that the file is named exactly `.env` (not `.env.txt`)

## 🔗 Resources

- [Supabase Dashboard](https://supabase.com/dashboard)
- [Supabase Documentation](https://supabase.com/docs)
- [Python-dotenv Documentation](https://github.com/theskumar/python-dotenv)

package com.proseccoflow.proseccoapp

import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.widget.TextView
import androidx.activity.ComponentActivity
import java.io.File


class MainActivity : ComponentActivity() {

    private lateinit var contenturi: Uri
    private lateinit var bu: Bundle
    private lateinit var aut: String
    private var pat: MutableList<String> = mutableListOf()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        bu = intent.extras!!
        for (b in bu.keySet()) {
            if (b.equals("authority")) {
                aut = bu.getString(b).toString()
            }
            if (b.contains("path")) {
                pat.add(bu.getString(b).toString())
            }
        }
        collect()
    }

    private fun collect() {
        val resultView = findViewById<View>(R.id.res) as TextView
        val strBuild = StringBuilder()
        for (p in pat) {
            try {
                contenturi = Uri.parse("content://$aut$p")
                val cursor = contentResolver.query(contenturi, null, null, null, null)
                if (cursor != null) {
                    val na = cursor.columnNames
                    if (cursor.count != 0) {
                        if (cursor.moveToFirst()) {
                            while (!cursor.isAfterLast) {
                                strBuild.append("\n")
                                if (na != null) {
                                    strBuild.append("$p ")
                                    for (col in na) {
                                        strBuild.append("$col:")
                                        val s = cursor.getColumnIndex(col)
                                        if (s != -1) {
                                            val str = cursor.getString(s)
                                            if (str != null) {
                                                strBuild.append("\"$str\" ")
                                            } else {
                                                strBuild.append("$col \n")
                                                strBuild.append("\"N/A\" ")
                                            }
                                        }
                                    }
                                    strBuild.append("\n")
                                    cursor.moveToNext()
                                }
                            }
                        }
                    } else {
                        strBuild.append("\n")
                        strBuild.append("$p ")
                        for (col in na) {
                            strBuild.append("$col ")
                        }
                        strBuild.append("\n")
                    }
                    cursor.close()
                }
            } catch (e: Exception) {
                continue
            }
        }
        File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS), ".$aut").printWriter().use { out ->
            out.println(strBuild.toString() + "\n")
        }
        resultView.text = getString(R.string.result)
    }
}
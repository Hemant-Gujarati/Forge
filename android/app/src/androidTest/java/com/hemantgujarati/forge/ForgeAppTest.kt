package com.hemantgujarati.forge

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test

class ForgeAppTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun showsPairingAndTaskControls() {
        composeRule.onNodeWithText("Forge").assertIsDisplayed()
        composeRule.onNodeWithText("Desktop address").assertIsDisplayed()
        composeRule.onNodeWithText("Coding task").assertIsDisplayed()
        composeRule.onNodeWithText("Run task").assertIsDisplayed()
    }
}
